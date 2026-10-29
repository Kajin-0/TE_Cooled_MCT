"""Reader labels and formal verdicts derived from preserved numerical records."""


def verification_matrix(summary, audit, limits):
    cases = summary['cases']
    rows = []

    def add(test, criterion, evidence, status, source):
        rows.append(dict(test=test, criterion=criterion, evidence=evidence,
                         status=status, source=source))

    def maximum(key):
        return max(abs(row[key]) for row in cases.values())

    def metric(test, key, limit, unit, source_check):
        value = maximum(key)
        passed = value < limit and all(row['checks'][source_check] for row in cases.values())
        exponent = int(f'{limit:.0e}'.split('e')[1])
        mantissa, power = f'{value:.2e}'.split('e')
        add(test, f'$<10^{{{exponent}}}$ {unit}',
            f'Maximum ${mantissa}'+r'\times10^{'+str(int(power))+'}$ '+unit,
            'PASS' if passed else 'FAIL', 'cases/*/metrics.json:' + key)

    mesh = summary['mesh_audits']['mesh_h0']
    add('Mesh / topology', 'Positive cells; conformal contacts; unique two-terminal path',
        '215 domains; 88 legs; 181 vertices / 180 edges',
        'PASS' if mesh['passed'] and mesh['graph']['unique_path'] else 'FAIL',
        'charts/summary.json:mesh_audits.mesh_h0')
    add('Field correspondence', r'Bijective nodes $\leq10^{-12}$ m; exact cells / bodies',
        r'Raw and derived fields agree; $\mathbf j,\mathbf q$ reconstructed',
        'PASS' if audit['passed'] else 'FAIL', 'report_inputs.json')
    cuts = 100 * maximum('worst_cut_relative_error')
    add('Interior current cuts', r'$<0.5\%$ driven; $<1\,\mu$A at zero drive',
        f'175 cuts; driven maximum {cuts:.3f}'+r'\%',
        'PASS' if all(x['checks']['driven_half_pct_or_zero_1uA_cuts'] for x in cases.values()) else 'FAIL',
        'cases/*/metrics.json:component_cuts')
    metric('Current balance', 'current_error_a', limits['free_current_a'], 'A', 'current_1uA')
    metric('Free current residual', 'free_current_residual_l1_a', limits['free_current_a'], 'A', 'free_current_1uA')
    metric('Free heat residual', 'free_thermal_residual_l1_w', limits['free_heat_w'], 'W', 'free_thermal_1uW')
    metric('Global energy balance', 'global_energy_error_w', limits['global_energy_w'], 'W', 'global_energy_1uW')
    bath = 100 * maximum('direct_bath_relative_error')
    add('Coarse bath gradient', r'$<1\%$ independent direct flux', f'Worst accepted case {bath:.3f}'+r'\%',
        'PASS' if bath < 100 * limits['direct_bath_relative'] else 'FAIL', 'cases/*/metrics.json:direct_bath_relative_error')
    plates = summary['independent_plate_checks']
    error = max(p['max_temperature_error_k'] for p in plates.values())
    mantissa, exponent = f'{error:.2e}'.split('e')
    add('Independent plate solves', r'$<10^{-6}$ K; heat balance $<10^{-9}$ W',
        f'Two Elmer references; maximum ${mantissa}'+r'\times10^{'+str(int(exponent))+'}$ K',
        'PASS' if all(p['passed'] for p in plates.values()) else 'FAIL', 'charts/summary.json:independent_plate_checks')
    checks = ('radiation_balance_1nW', 'gas_balance_1nW', 'hybrid_balance_1nW', 'lead_joule_balance_1nW')
    exchange_cases = {name: row for name, row in cases.items()
                      if 'radiation_balance_1nW' in row['checks']}
    add('Internal exchange balance', r'$<10^{-9}$ W per mechanism',
        f'{len(exchange_cases)} exchange-operator cases; radiation, gas, Au/Cu',
        'PASS' if exchange_cases and all(all(r['checks'][k] for k in checks) for r in exchange_cases.values()) else 'FAIL',
        'cases/{'+','.join(exchange_cases)+'}/metrics.json:checks')
    surface = summary['surface_refinement']
    add('Surface refinement', r'$<1\%$ of lift; $<1\%$ voltage change',
        f"442 to 907 patches: {100*surface['max_change_over_lift']:.3f}"+r'\% lift; '+f"{100*surface['voltage_relative_change']:.3f}"+r'\% voltage',
        'PASS' if surface['passed'] else 'FAIL', 'charts/summary.json:surface_refinement')
    values = [100*r['direct_bath_relative_error'] for r in summary['unaccepted_fine_cases'].values()]
    add('Fine bath gradient', r'$<1\%$ independent direct flux',
        f'Three converged meshes: {min(values):.2f}--{max(values):.2f}'+r'\%',
        'FAIL' if any(abs(v) >= 100*limits['direct_bath_relative'] for v in values) else 'PASS',
        'charts/summary.json:unaccepted_fine_cases')
    add('Fine-mesh qualification', 'Every declared numerical gate must pass',
        'Independent bath-gradient criterion fails',
        'NOT QUALIFIED' if not summary['full_g3b_qualified'] else 'PASS', 'charts/summary.json:full_g3b_qualified')
    add('Manufacturer / device accuracy', 'Matched materials, interfaces and independent device data',
        'No qualified full-device comparison',
        'NOT QUALIFIED' if not summary['device_validated'] else 'PASS', 'charts/summary.json:device_validated')
    return rows
