"""
maestros/management/commands/seed_contab_config.py — Sprint A · A1

Uso:
    python manage.py seed_contab_config             # carga sólo lo que falta
    python manage.py seed_contab_config --force     # reescribe todo desde defaults
    python manage.py seed_contab_config --dry-run   # muestra plan sin tocar DB

Pensado para ejecutarse una sola vez post-migración Sprint A. Carga la
configuración inicial usando los códigos de cuenta que estaban hardcoded
en el dict CA={...} de la versión anterior. Después el contador puede
ajustar vía /api/contab/Config/Cuentas/.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from maestros.contabilidad_models import (
    ContabConfigCuenta, ContabPlanCuentas
)


# Mapeo: concepto canónico → código de cuenta default
# Replicamos el dict CA original + agregamos los nuevos conceptos (todos opcionales).
SEED_DEFAULTS = {
    # ── Disponibilidades (CA legacy) ─────────────────────────────────────
    'CAJA':                  '1.1.01.001',
    'BANCO_DEFAULT':         '1.1.01.002',

    # ── Créditos ────────────────────────────────────────────────────────
    'DEUDORES_CC':           '1.1.03.001',

    # ── IVA Crédito Fiscal (default a 21%) ──────────────────────────────
    'IVA_CF_21':             '1.1.04.001',

    # ── Bienes de Cambio ────────────────────────────────────────────────
    'MERCADERIAS_DEFAULT':   '1.1.05.001',

    # ── Pasivos comerciales ─────────────────────────────────────────────
    'PROVEEDORES':           '2.1.01.001',

    # ── IVA Débito Fiscal ───────────────────────────────────────────────
    'IVA_DF_21':             '2.1.02.001',

    # ── Ingresos ────────────────────────────────────────────────────────
    'VENTAS_21':             '4.1.01.001',
    'VENTAS_10_5':           '4.1.01.002',
    'VENTAS_EXENTAS':        '4.1.01.003',

    # ── PN ──────────────────────────────────────────────────────────────
    'RESULTADO_NO_ASIGNADO': '3.3.01.001',
}


class Command(BaseCommand):
    help = 'Inicializa la tabla ContabConfigCuenta con los valores que estaban hardcoded.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force', action='store_true',
            help='Sobrescribe entradas existentes (default: solo carga las faltantes).'
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Muestra el plan sin escribir en la base.'
        )
        parser.add_argument(
            '--quiet', action='store_true',
            help='Reduce verbosidad.'
        )

    def handle(self, *args, **options):
        force   = options['force']
        dry_run = options['dry_run']
        quiet   = options['quiet']

        if not quiet:
            self.stdout.write(self.style.MIGRATE_HEADING(
                '\n=== Sprint A · seed_contab_config ===\n'
            ))

        # Verificar que las cuentas referenciadas existan
        codigos_referenciados = set(SEED_DEFAULTS.values())
        cuentas_existentes = set(
            ContabPlanCuentas.objects.filter(codigo__in=codigos_referenciados)
                                     .values_list('codigo', flat=True)
        )
        cuentas_faltantes = codigos_referenciados - cuentas_existentes

        if cuentas_faltantes:
            self.stdout.write(self.style.ERROR(
                f"\n❌ Las siguientes cuentas NO existen en el plan:"
            ))
            for c in sorted(cuentas_faltantes):
                self.stdout.write(f"     • {c}")
            self.stdout.write(self.style.WARNING(
                "\nCargue el plan de cuentas primero (POST /api/contab/GuardarCuenta/)\n"
                "o ajuste el SEED_DEFAULTS de este comando.\n"
            ))
            return

        existentes_pre = set(
            ContabConfigCuenta.objects.values_list('concepto', flat=True)
        )

        plan = []
        for concepto, codigo_cuenta in SEED_DEFAULTS.items():
            ya_existe = concepto in existentes_pre
            if ya_existe and not force:
                plan.append(('SKIP', concepto, codigo_cuenta, 'ya configurado'))
            else:
                accion = 'UPDATE' if ya_existe else 'CREATE'
                plan.append((accion, concepto, codigo_cuenta, ''))

        if not quiet:
            self.stdout.write("\nPlan de ejecución:")
            for accion, concepto, codigo, nota in plan:
                color = {
                    'CREATE': self.style.SUCCESS,
                    'UPDATE': self.style.WARNING,
                    'SKIP':   self.style.NOTICE,
                }[accion]
                self.stdout.write(
                    f"  {color(accion):16} {concepto:32} → {codigo:14} {nota}"
                )

        if dry_run:
            self.stdout.write(self.style.WARNING(
                "\n⚠ --dry-run activo. No se escribió nada en la base.\n"
            ))
            return

        # Aplicar cambios
        creados = actualizados = saltados = 0
        with transaction.atomic():
            for accion, concepto, codigo_cuenta, _ in plan:
                if accion == 'SKIP':
                    saltados += 1
                    continue
                ContabConfigCuenta.objects.update_or_create(
                    concepto=concepto,
                    defaults={
                        'cuenta_id':         codigo_cuenta,
                        'descripcion_extra': 'Cargado por seed_contab_config (Sprint A)',
                        'usuario':           'seed',
                    }
                )
                if accion == 'CREATE':
                    creados += 1
                else:
                    actualizados += 1

        if not quiet:
            self.stdout.write(self.style.SUCCESS(
                f"\n✓ Listo: {creados} creados · {actualizados} actualizados · {saltados} saltados.\n"
                f"  Conceptos cubiertos: {len(SEED_DEFAULTS)} de "
                f"{len(ContabConfigCuenta.CONCEPTO_CHOICES)} disponibles.\n"
                f"  El resto se puede cargar desde "
                f"GET /api/contab/Config/Estado/ y POST /api/contab/Config/Cuentas/.\n"
            ))