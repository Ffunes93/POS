"""
maestros/tests/test_contab_sprint_a.py — Sprint A

Cubre los 5 fixes principales:
  A1 — ContabConfigCuenta resuelve cuentas correctamente
  A2 — _generar_asiento_venta usa ImpIVAAlicuotas (multi-alícuota + fallback)
  A3 — UniqueConstraint en BD bloquea duplicados; anulación libera el slot
  A4 — Apertura y Cierre filtran SOLO el ejercicio correspondiente
  A5 — ContabAuth funciona en modo estricto y permisivo

Ejecutar:
    python manage.py test maestros.tests.test_contab_sprint_a
"""
from datetime import date
from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.contrib.auth.models import AnonymousUser, User

from maestros.models import (
    ContabPlanCuentas, ContabAsiento, ContabAsientoDet,
    ContabEjercicio, ContabConfigCuenta,
    ContabTipoAsiento, ContabSerieAsiento,
    Ventas,
)
from maestros.impositivo_models import ImpIVAAlicuotas
from maestros.permissions import ContabAuth, get_usuario_actual
from maestros.views.contabilidad import (
    _generar_asiento_venta, _config, _cuenta, _key_alicuota,
    _asiento_apertura, _asiento_cierre,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixture común
# ─────────────────────────────────────────────────────────────────────────────

class _BaseContabTest(TestCase):
    """Setup común: plan de cuentas mínimo + config + tipos/series + ejercicios."""

    @classmethod
    def setUpTestData(cls):
        # Plan de cuentas mínimo
        cuentas_def = [
            ('1.1.01.001', 'Caja',                  'A',  'D'),
            ('1.1.01.002', 'Banco',                 'A',  'D'),
            ('1.1.03.001', 'Deudores por ventas',   'A',  'D'),
            ('1.1.04.001', 'IVA Crédito Fiscal 21', 'A',  'D'),
            ('1.1.04.002', 'IVA Crédito Fiscal 10.5','A', 'D'),
            ('1.1.05.001', 'Mercaderías',           'A',  'D'),
            ('2.1.01.001', 'Proveedores',           'P',  'C'),
            ('2.1.02.001', 'IVA Débito Fiscal 21',  'P',  'C'),
            ('2.1.02.002', 'IVA Débito Fiscal 10.5','P',  'C'),
            ('2.1.05.001', 'Percepción IIBB CABA',  'P',  'C'),
            ('3.3.01.001', 'Resultado No Asignado', 'PN', 'C'),
            ('3.3.02.001', 'Resultado del Ejercicio','PN','C'),
            ('4.1.01.001', 'Ventas 21%',            'I',  'C'),
            ('4.1.01.002', 'Ventas 10.5%',          'I',  'C'),
            ('4.1.01.003', 'Ventas Exentas',        'I',  'C'),
            ('5.1.01.001', 'Costo Mercaderías',     'E',  'D'),
            ('5.9.01.001', 'Diferencia de redondeo','E',  'D'),
        ]
        for cod, nom, tipo, sal in cuentas_def:
            ContabPlanCuentas.objects.create(
                codigo=cod, nombre=nom, tipo=tipo, nivel=4,
                es_imputable=True, saldo_tipo=sal, activa=True,
            )

        # Config (lo mínimo para que los tests funcionen)
        configs = [
            ('CAJA',                            '1.1.01.001'),
            ('BANCO_DEFAULT',                   '1.1.01.002'),
            ('DEUDORES_CC',                     '1.1.03.001'),
            ('IVA_CF_21',                       '1.1.04.001'),
            ('IVA_CF_10_5',                     '1.1.04.002'),
            ('MERCADERIAS_DEFAULT',             '1.1.05.001'),
            ('PROVEEDORES',                     '2.1.01.001'),
            ('IVA_DF_21',                       '2.1.02.001'),
            ('IVA_DF_10_5',                     '2.1.02.002'),
            ('PERCEPCION_IIBB_CABA_PRACTICADA', '2.1.05.001'),
            ('RESULTADO_NO_ASIGNADO',           '3.3.01.001'),
            ('RESULTADO_DEL_EJERCICIO',         '3.3.02.001'),
            ('VENTAS_21',                       '4.1.01.001'),
            ('VENTAS_10_5',                     '4.1.01.002'),
            ('VENTAS_EXENTAS',                  '4.1.01.003'),
            ('DIFERENCIA_REDONDEO',             '5.9.01.001'),
        ]
        for concepto, codigo in configs:
            ContabConfigCuenta.objects.create(
                concepto=concepto, cuenta_id=codigo, usuario='test'
            )

        # Tipos y series
        ContabTipoAsiento.objects.create(codigo='001', descripcion='Real')
        ContabSerieAsiento.objects.create(codigo='DIA', descripcion='Diario',
                                           ultimo_nro=0)

        # Ejercicios
        cls.ej_2024 = ContabEjercicio.objects.create(
            anio_inicio=2024, anio_fin=2024,
            fecha_inicio=date(2024, 1, 1), fecha_fin=date(2024, 12, 31),
            estado='C',
        )
        cls.ej_2025 = ContabEjercicio.objects.create(
            anio_inicio=2025, anio_fin=2025,
            fecha_inicio=date(2025, 1, 1), fecha_fin=date(2025, 12, 31),
            estado='A',
        )

    def _crear_venta(self, movim=1001, total='1210.00', neto='1000.00',
                     iva='210.00', cond='1', exento='0', perce_caba='0',
                     fecha=None):
        """Helper para crear una venta legacy mock."""
        return Ventas.objects.create(
            movim=movim,
            cod_comprob='FCA',
            nro_comprob=f'00001-{movim:08d}',
            fecha_fact=fecha or date(2025, 6, 15),
            cliente=1,
            tot_general=Decimal(total),
            neto=Decimal(neto),
            iva_1=Decimal(iva),
            exento=Decimal(exento),
            perce_caba=Decimal(perce_caba),
            cond_venta=cond,
            anulado='N',
            usuario='test',
        )


# ─────────────────────────────────────────────────────────────────────────────
# A1 — Configuración de cuentas
# ─────────────────────────────────────────────────────────────────────────────

class TestA1ConfigCuentas(_BaseContabTest):

    def test_config_carga_mapa_completo(self):
        config = _config()
        self.assertEqual(config['CAJA'],         '1.1.01.001')
        self.assertEqual(config['DEUDORES_CC'],  '1.1.03.001')
        self.assertEqual(config['VENTAS_21'],    '4.1.01.001')
        self.assertEqual(config['VENTAS_10_5'],  '4.1.01.002')
        self.assertEqual(config['IVA_DF_21'],    '2.1.02.001')

    def test_cuenta_obligatoria_falla_si_no_existe(self):
        config = _config()
        with self.assertRaises(ValueError) as ctx:
            _cuenta(config, 'CONCEPTO_INEXISTENTE', requerida=True)
        self.assertIn('no configurado', str(ctx.exception))

    def test_cuenta_opcional_devuelve_none(self):
        config = _config()
        self.assertIsNone(_cuenta(config, 'CONCEPTO_INEXISTENTE'))

    def test_db_pisa_fallback(self):
        # CA_FALLBACK tiene CAJA=1.1.01.001; sobreescribimos en DB
        ContabPlanCuentas.objects.create(
            codigo='9.9.99.999', nombre='Caja Custom', tipo='A',
            nivel=4, saldo_tipo='D', es_imputable=True,
        )
        ContabConfigCuenta.objects.filter(concepto='CAJA').update(cuenta_id='9.9.99.999')

        config = _config()
        self.assertEqual(config['CAJA'], '9.9.99.999')

    def test_get_cuenta_obligatoria_raise(self):
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            ContabConfigCuenta.obtener_cuenta_obligatoria('NO_EXISTE_NUNCA')


# ─────────────────────────────────────────────────────────────────────────────
# A2 — Generador de venta usa ImpIVAAlicuotas
# ─────────────────────────────────────────────────────────────────────────────

class TestA2GeneradorVenta(_BaseContabTest):

    def test_key_alicuota(self):
        self.assertEqual(_key_alicuota(Decimal('21.00')), '21')
        self.assertEqual(_key_alicuota(Decimal('10.50')), '10_5')
        self.assertEqual(_key_alicuota(Decimal('27.00')), '27')
        self.assertEqual(_key_alicuota(Decimal('2.50')),  '2_5')
        self.assertEqual(_key_alicuota(Decimal('0.00')),  '0')

    def test_venta_con_alicuotas_multiples_genera_lineas_correctas(self):
        """Venta con 21% y 10.5% → genera líneas separadas en ventas e IVA DF."""
        venta = self._crear_venta(movim=2001, total='1320.00', neto='1100.00',
                                   iva='220.00')
        # Discriminación: $500 al 21% + $600 al 10.5%
        ImpIVAAlicuotas.objects.create(
            circuito='V', movim=2001, alicuota=Decimal('21.00'),
            neto_gravado=Decimal('500.00'), iva=Decimal('105.00'),
            nro_renglon=1,
        )
        ImpIVAAlicuotas.objects.create(
            circuito='V', movim=2001, alicuota=Decimal('10.50'),
            neto_gravado=Decimal('600.00'), iva=Decimal('63.00'),
            nro_renglon=2,
        )
        # Ajuste: el total = 500+105 + 600+63 = 1268, no 1320. Para el test
        # importa que se generen las líneas correctas, la diferencia va a redondeo.

        asiento = _generar_asiento_venta(venta)
        self.assertIsNotNone(asiento)

        cuentas_haber = {l.cuenta_id: l.haber for l in asiento.lineas.filter(haber__gt=0)}
        # Debe haber líneas para VENTAS_21, VENTAS_10_5, IVA_DF_21, IVA_DF_10_5
        self.assertIn('4.1.01.001', cuentas_haber)  # ventas 21
        self.assertIn('4.1.01.002', cuentas_haber)  # ventas 10.5
        self.assertIn('2.1.02.001', cuentas_haber)  # IVA DF 21
        self.assertIn('2.1.02.002', cuentas_haber)  # IVA DF 10.5
        self.assertEqual(cuentas_haber['4.1.01.001'], Decimal('500.00'))
        self.assertEqual(cuentas_haber['4.1.01.002'], Decimal('600.00'))

    def test_venta_sin_alicuotas_usa_fallback_21(self):
        """Si ImpIVAAlicuotas no tiene filas, usa cálculo legacy."""
        venta = self._crear_venta(movim=2002, total='1210.00',
                                   neto='1000.00', iva='210.00')

        asiento = _generar_asiento_venta(venta)
        self.assertIsNotNone(asiento)

        cuentas_haber = {l.cuenta_id: l.haber for l in asiento.lineas.filter(haber__gt=0)}
        self.assertIn('4.1.01.001', cuentas_haber)
        self.assertEqual(cuentas_haber['4.1.01.001'], Decimal('1000.00'))
        self.assertEqual(cuentas_haber['2.1.02.001'], Decimal('210.00'))

    def test_venta_con_exento_imputa_a_ventas_exentas(self):
        venta = self._crear_venta(movim=2003, total='1500.00', neto='1000.00',
                                   iva='210.00', exento='290.00')

        asiento = _generar_asiento_venta(venta)
        cuentas_haber = {l.cuenta_id: l.haber for l in asiento.lineas.filter(haber__gt=0)}
        self.assertIn('4.1.01.003', cuentas_haber)
        self.assertEqual(cuentas_haber['4.1.01.003'], Decimal('290.00'))

    def test_venta_con_percepcion_caba_imputa_a_pasivo(self):
        venta = self._crear_venta(movim=2004, total='1260.00', neto='1000.00',
                                   iva='210.00', perce_caba='50.00')

        asiento = _generar_asiento_venta(venta)
        cuentas_haber = {l.cuenta_id: l.haber for l in asiento.lineas.filter(haber__gt=0)}
        self.assertIn('2.1.05.001', cuentas_haber)
        self.assertEqual(cuentas_haber['2.1.05.001'], Decimal('50.00'))

    def test_asiento_cuadra(self):
        venta = self._crear_venta(movim=2005, total='1210.00', neto='1000.00',
                                   iva='210.00')
        asiento = _generar_asiento_venta(venta)
        self.assertTrue(asiento.cuadra,
                        f"D={asiento.total_debe} H={asiento.total_haber}")


# ─────────────────────────────────────────────────────────────────────────────
# A3 — Idempotencia y UniqueConstraint
# ─────────────────────────────────────────────────────────────────────────────

class TestA3Idempotencia(_BaseContabTest):

    def test_no_duplica_al_llamar_dos_veces(self):
        venta = self._crear_venta(movim=3001)
        a1 = _generar_asiento_venta(venta)
        a2 = _generar_asiento_venta(venta)
        self.assertIsNotNone(a1)
        self.assertIsNone(a2)  # ya existía → devuelve None

        cnt = ContabAsiento.objects.filter(
            origen='VTA', origen_movim=3001, anulado=False
        ).count()
        self.assertEqual(cnt, 1)

    def test_uniqueconstraint_db_rechaza_duplicado_directo(self):
        """Crear 2 asientos VTA con mismo origen_movim no anulado → IntegrityError."""
        venta = self._crear_venta(movim=3002)
        _generar_asiento_venta(venta)

        # Intento crear uno paralelo manualmente
        with self.assertRaises(IntegrityError):
            ContabAsiento.objects.create(
                fecha=date(2025, 6, 15),
                descripcion='Duplicado ilegal',
                origen='VTA', origen_movim=3002,
                anulado=False, estado='M',
            )

    def test_anulacion_libera_origen_movim_activo(self):
        """Tras anular, se puede regenerar otro asiento con el mismo origen_movim."""
        venta = self._crear_venta(movim=3003)
        a1 = _generar_asiento_venta(venta)
        self.assertIsNotNone(a1)
        self.assertEqual(a1.origen_movim_activo, 3003)

        # Anulamos
        a1.anulado = True
        a1.save()
        a1.refresh_from_db()
        self.assertIsNone(a1.origen_movim_activo)

        # Regenerar funciona
        a2 = _generar_asiento_venta(venta)
        self.assertIsNotNone(a2)
        self.assertNotEqual(a1.id, a2.id)
        self.assertEqual(a2.origen_movim_activo, 3003)

    def test_multiples_anulados_pueden_coexistir(self):
        """Dos asientos anulados con mismo origen_movim no rompen UNIQUE (NULL libre)."""
        for i in range(3):
            ContabAsiento.objects.create(
                fecha=date(2025, 6, 15),
                descripcion=f'Anulado {i}',
                origen='VTA', origen_movim=3004,
                anulado=True, estado='A',
            )
        # No debería lanzar excepción
        cnt = ContabAsiento.objects.filter(origen='VTA', origen_movim=3004).count()
        self.assertEqual(cnt, 3)


# ─────────────────────────────────────────────────────────────────────────────
# A4 — Apertura y Cierre filtran por ejercicio
# ─────────────────────────────────────────────────────────────────────────────

class TestA4AperturaCierre(_BaseContabTest):

    def _crear_asiento_simple(self, fecha, debe_cuenta, haber_cuenta, importe):
        """Crea un asiento simple D/H mayorizado para los fixtures."""
        a = ContabAsiento.objects.create(
            fecha=fecha, descripcion='Movimiento test',
            origen='AJU', estado='M', anulado=False,
            ejercicio=ContabEjercicio.objects.filter(
                fecha_inicio__lte=fecha, fecha_fin__gte=fecha
            ).first(),
        )
        ContabAsientoDet.objects.create(
            asiento=a, cuenta_id=debe_cuenta, debe=Decimal(str(importe)), haber=0,
        )
        ContabAsientoDet.objects.create(
            asiento=a, cuenta_id=haber_cuenta, debe=0, haber=Decimal(str(importe)),
        )
        return a

    def test_apertura_requiere_ejercicio_id(self):
        resp = _asiento_apertura(date(2026, 1, 1), 'test', None)
        self.assertEqual(resp.status_code, 400)
        self.assertIn('ejercicio_id', resp.data['error'])

    def test_apertura_filtra_solo_ejercicio_anterior(self):
        # Movimientos en 2024 (ej cerrado) y 2025 (ej activo)
        self._crear_asiento_simple(date(2024, 6, 1),  '1.1.01.001', '4.1.01.001', '1000')
        self._crear_asiento_simple(date(2025, 6, 1),  '1.1.01.001', '4.1.01.001', '5000')

        # Crear ejercicio nuevo 2026
        ej_2026 = ContabEjercicio.objects.create(
            anio_inicio=2026, anio_fin=2026,
            fecha_inicio=date(2026, 1, 1), fecha_fin=date(2026, 12, 31),
            estado='A',
        )

        # Apertura del 2026 debe tomar saldos del 2025 (no del 2024)
        resp = _asiento_apertura(date(2026, 1, 1), 'test', ej_2026.id)
        self.assertEqual(resp.status_code, 200)

        # Verificar: la caja debería tener el saldo SOLO del ejercicio anterior (2025)
        asiento_apertura = ContabAsiento.objects.filter(origen='APE').last()
        self.assertIsNotNone(asiento_apertura)

        linea_caja = asiento_apertura.lineas.filter(cuenta_id='1.1.01.001').first()
        self.assertIsNotNone(linea_caja)
        self.assertEqual(linea_caja.debe, Decimal('5000.00'))  # solo 2025

    def test_cierre_filtra_solo_ejercicio_indicado(self):
        # Movimientos en 2024 y 2025 — el cierre de 2025 NO debe traer 2024
        self._crear_asiento_simple(date(2024, 6, 1), '1.1.01.001', '4.1.01.001', '999')
        self._crear_asiento_simple(date(2025, 3, 1), '1.1.01.001', '4.1.01.001', '1000')
        self._crear_asiento_simple(date(2025, 9, 1), '1.1.01.001', '4.1.01.001', '2000')

        resp = _asiento_cierre(date(2025, 12, 31), 'test', self.ej_2025.id)
        self.assertEqual(resp.status_code, 200)
        # Resultado neto = 3000 (solo del 2025)
        self.assertEqual(resp.data['resultado_neto'], 3000.0)

    def test_cierre_requiere_ejercicio_id(self):
        resp = _asiento_cierre(date(2025, 12, 31), 'test', None)
        self.assertEqual(resp.status_code, 400)


# ─────────────────────────────────────────────────────────────────────────────
# A5 — Auth opt-in
# ─────────────────────────────────────────────────────────────────────────────

class TestA5Auth(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user('contador', password='x')

    @override_settings(CONTAB_REQUIRE_AUTH=False)
    def test_modo_legacy_permite_anonimo(self):
        request = self.factory.get('/api/contab/foo/')
        request.user = AnonymousUser()
        self.assertTrue(ContabAuth().has_permission(request, None))

    @override_settings(CONTAB_REQUIRE_AUTH=True)
    def test_modo_estricto_rechaza_anonimo(self):
        request = self.factory.get('/api/contab/foo/')
        request.user = AnonymousUser()
        self.assertFalse(ContabAuth().has_permission(request, None))

    @override_settings(CONTAB_REQUIRE_AUTH=True)
    def test_modo_estricto_acepta_autenticado(self):
        request = self.factory.get('/api/contab/foo/')
        request.user = self.user
        self.assertTrue(ContabAuth().has_permission(request, None))

    @override_settings(CONTAB_REQUIRE_AUTH=False)
    def test_get_usuario_legacy_acepta_payload(self):
        request = self.factory.post('/api/contab/foo/', {'usuario': 'manual'},
                                     content_type='application/json')
        request.user = AnonymousUser()
        request.data = {'usuario': 'manual'}
        u = get_usuario_actual(request)
        self.assertEqual(u, 'manual')

    @override_settings(CONTAB_REQUIRE_AUTH=True)
    def test_get_usuario_estricto_ignora_payload(self):
        """En modo estricto NO acepta payload['usuario'] (anti-suplantación)."""
        request = self.factory.post('/api/contab/foo/', {'usuario': 'admin_falso'},
                                     content_type='application/json')
        request.user = AnonymousUser()
        request.data = {'usuario': 'admin_falso'}
        u = get_usuario_actual(request)
        self.assertEqual(u, 'anon')   # NO 'admin_falso'

    @override_settings(CONTAB_REQUIRE_AUTH=True)
    def test_get_usuario_estricto_usa_request_user(self):
        request = self.factory.post('/api/contab/foo/')
        request.user = self.user
        request.data = {}
        u = get_usuario_actual(request)
        self.assertEqual(u, 'contador')