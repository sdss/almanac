#from itertools import batched
from typing import List
from peewee import JOIN

from itertools import islice
import concurrent.futures

def batched(iterable, n):
    it = iter(iterable)
    while True:
        batch = tuple(islice(it, n))
        if not batch:
            return
        yield batch


def _query_single_batch(batch):
    """Query a single batch of SDSS IDs. Helper for parallelization."""
    from almanac.database import catalogdb as db

    q = (
        db
        .SDSS_ID_To_Catalog
        .select(
            db.SDSS_ID_To_Catalog.sdss_id,
            db.SDSS_ID_To_Catalog.catalogid,
            db.SDSS_ID_To_Catalog.version_id,
            db.SDSS_ID_To_Catalog.lead,
            db.SDSS_ID_To_Catalog.allstar_dr17_synspec_rev1,
            db.SDSS_ID_To_Catalog.allwise,
            db.SDSS_ID_To_Catalog.bhm_rm_v0,
            db.SDSS_ID_To_Catalog.bhm_rm_v0_2,
            db.SDSS_ID_To_Catalog.catwise,
            db.SDSS_ID_To_Catalog.catwise2020,
            db.SDSS_ID_To_Catalog.gaia_dr2_source,
            db.SDSS_ID_To_Catalog.gaia_dr3_source,
            db.SDSS_ID_To_Catalog.glimpse,
            db.SDSS_ID_To_Catalog.guvcat,
            db.SDSS_ID_To_Catalog.legacy_survey_dr10,
            db.SDSS_ID_To_Catalog.legacy_survey_dr8,
            db.SDSS_ID_To_Catalog.mangatarget,
            db.SDSS_ID_To_Catalog.marvels_dr11_star,
            db.SDSS_ID_To_Catalog.marvels_dr12_star,
            db.SDSS_ID_To_Catalog.mastar_goodstars,
            db.SDSS_ID_To_Catalog.panstarrs1,
            db.SDSS_ID_To_Catalog.ps1_g18,
            db.SDSS_ID_To_Catalog.sdss_dr13_photoobj,
            db.SDSS_ID_To_Catalog.sdss_dr17_specobj,
            db.SDSS_ID_To_Catalog.skymapper_dr1_1,
            db.SDSS_ID_To_Catalog.skymapper_dr2,
            db.SDSS_ID_To_Catalog.supercosmos,
            db.SDSS_ID_To_Catalog.tic_v8,
            db.SDSS_ID_To_Catalog.twomass_psc,
            db.SDSS_ID_To_Catalog.tycho2,
            db.SDSS_ID_To_Catalog.unwise,
            db.Gaia_DR3.source_id.alias('gaia_source_id'),
            db.Gaia_DR3.solution_id.alias('gaia_solution_id'),
            db.Gaia_DR3.ra.alias('gaia_ra'),
            db.Gaia_DR3.ra_error.alias('gaia_ra_error'),
            db.Gaia_DR3.dec.alias('gaia_dec'),
            db.Gaia_DR3.dec_error.alias('gaia_dec_error'),
            db.Gaia_DR3.parallax.alias('gaia_parallax'),
            db.Gaia_DR3.parallax_error.alias('gaia_parallax_error'),
            db.Gaia_DR3.pm.alias('gaia_pm'),
            db.Gaia_DR3.pmra.alias('gaia_pmra'),
            db.Gaia_DR3.pmra_error.alias('gaia_pmra_error'),
            db.Gaia_DR3.pmdec.alias('gaia_pmdec'),
            db.Gaia_DR3.pmdec_error.alias('gaia_pmdec_error'),
            db.Gaia_DR3.ruwe.alias('gaia_ruwe'),
            db.Gaia_DR3.duplicated_source.alias('gaia_duplicated_source'),
            db.Gaia_DR3.phot_g_mean_mag.alias('gaia_phot_g_mean_mag'),
            db.Gaia_DR3.phot_bp_mean_mag.alias('gaia_phot_bp_mean_mag'),
            db.Gaia_DR3.phot_rp_mean_mag.alias('gaia_phot_rp_mean_mag'),
            db.Gaia_DR3.phot_bp_rp_excess_factor.alias('gaia_phot_bp_rp_excess_factor'),
            db.Gaia_DR3.radial_velocity.alias('gaia_radial_velocity'),
            db.Gaia_DR3.radial_velocity_error.alias('gaia_radial_velocity_error'),
            db.Gaia_DR3.rv_nb_transits.alias('gaia_rv_nb_transits'),
            #db.Gaia_DR3.rv_method_used.alias('gaia_rv_method_used'),
            #db.Gaia_DR3.rv_nb_deblended_transits.alias('gaia_rv_nb_deblended_transits'),
            #db.Gaia_DR3.rv_visibility_periods_used.alias('gaia_rv_visibility_periods_used'),
            #db.Gaia_DR3.rv_expected_sig_to_noise.alias('gaia_rv_expected_sig_to_noise'),
            #db.Gaia_DR3.rv_renormalised_gof.alias('gaia_rv_renormalised_gof'),
            #db.Gaia_DR3.rv_chisq_pvalue.alias('gaia_rv_chisq_pvalue'),
            #db.Gaia_DR3.rv_time_duration.alias('gaia_rv_time_duration'),
            #db.Gaia_DR3.rv_amplitude_robust.alias('gaia_rv_amplitude_robust'),
            db.Gaia_DR3.rv_template_teff.alias('gaia_rv_template_teff'),
            db.Gaia_DR3.rv_template_logg.alias('gaia_rv_template_logg'),
            db.Gaia_DR3.rv_template_fe_h.alias('gaia_rv_template_fe_h'),
            db.Gaia_DR3.rv_atm_param_origin.alias('gaia_rv_atm_param_origin'),
            db.Gaia_DR3.vbroad.alias('gaia_vbroad'),
            db.Gaia_DR3.vbroad_error.alias('gaia_vbroad_error'),
            db.Gaia_DR3.vbroad_nb_transits.alias('gaia_vbroad_nb_transits'),
            db.Gaia_DR3.grvs_mag.alias('gaia_grvs_mag'),
            db.Gaia_DR3.grvs_mag_error.alias('gaia_grvs_mag_error'),
            db.Gaia_DR3.grvs_mag_nb_transits.alias('gaia_grvs_mag_nb_transits'),
            db.Gaia_DR3.rvs_spec_sig_to_noise.alias('gaia_rvs_spec_sig_to_noise'),
            db.Gaia_DR3.phot_variable_flag.alias('gaia_phot_variable_flag'),
            #db.Gaia_DR3.l.alias('gaia_l'),
            #db.Gaia_DR3.b.alias('gaia_b'),
            #db.Gaia_DR3.ecl_lon.alias('gaia_ecl_lon'),
            #db.Gaia_DR3.ecl_lat.alias('gaia_ecl_lat'),
            #db.Gaia_DR3.in_qso_candidates.alias('gaia_in_qso_candidates'),
            #db.Gaia_DR3.in_galaxy_candidates.alias('gaia_in_galaxy_candidates'),
            #db.Gaia_DR3.non_single_star.alias('gaia_non_single_star'),
            #db.Gaia_DR3.has_xp_continuous.alias('gaia_has_xp_continuous'),
            #db.Gaia_DR3.has_xp_sampled.alias('gaia_has_xp_sampled'),
            #db.Gaia_DR3.has_rvs.alias('gaia_has_rvs'),
            #db.Gaia_DR3.has_epoch_photometry.alias('gaia_has_epoch_photometry'),
            #db.Gaia_DR3.has_epoch_rv.alias('gaia_has_epoch_rv'),
            #db.Gaia_DR3.has_mcmc_gspphot.alias('gaia_has_mcmc_gspphot'),
            #db.Gaia_DR3.has_mcmc_msc.alias('gaia_has_mcmc_msc'),
            #db.Gaia_DR3.in_andromeda_survey.alias('gaia_in_andromeda_survey'),
            #db.Gaia_DR3.classprob_dsc_combmod_quasar.alias('gaia_classprob_dsc_combmod_quasar'),
            #db.Gaia_DR3.classprob_dsc_combmod_galaxy.alias('gaia_classprob_dsc_combmod_galaxy'),
            #db.Gaia_DR3.classprob_dsc_combmod_star.alias('gaia_classprob_dsc_combmod_star'),
            db.Gaia_DR3.teff_gspphot.alias('gaia_teff_gspphot'),
            #db.Gaia_DR3.teff_gspphot_lower.alias('gaia_teff_gspphot_lower'),
            #db.Gaia_DR3.teff_gspphot_upper.alias('gaia_teff_gspphot_upper'),
            db.Gaia_DR3.logg_gspphot.alias('gaia_logg_gspphot'),
            #db.Gaia_DR3.logg_gspphot_lower.alias('gaia_logg_gspphot_lower'),
            #db.Gaia_DR3.logg_gspphot_upper.alias('gaia_logg_gspphot_upper'),
            db.Gaia_DR3.mh_gspphot.alias('gaia_mh_gspphot'),
            #db.Gaia_DR3.mh_gspphot_lower.alias('gaia_mh_gspphot_lower'),
            #db.Gaia_DR3.mh_gspphot_upper.alias('gaia_mh_gspphot_upper'),
            db.Gaia_DR3.distance_gspphot.alias('gaia_distance_gspphot'),
            #db.Gaia_DR3.distance_gspphot_lower.alias('gaia_distance_gspphot_lower'),
            #db.Gaia_DR3.distance_gspphot_upper.alias('gaia_distance_gspphot_upper'),
            db.Gaia_DR3.azero_gspphot.alias('gaia_azero_gspphot'),
            #db.Gaia_DR3.azero_gspphot_lower.alias('gaia_azero_gspphot_lower'),
            #db.Gaia_DR3.azero_gspphot_upper.alias('gaia_azero_gspphot_upper'),
            db.Gaia_DR3.ag_gspphot.alias('gaia_ag_gspphot'),
            #db.Gaia_DR3.ag_gspphot_lower.alias('gaia_ag_gspphot_lower'),
            #db.Gaia_DR3.ag_gspphot_upper.alias('gaia_ag_gspphot_upper'),
            #db.Gaia_DR3.ebpminrp_gspphot.alias('gaia_ebpminrp_gspphot'),
            #db.Gaia_DR3.ebpminrp_gspphot_lower.alias('gaia_ebpminrp_gspphot_lower'),
            #db.Gaia_DR3.ebpminrp_gspphot_upper.alias('gaia_ebpminrp_gspphot_upper'),
            #db.Gaia_DR3.libname_gspphot.alias('gaia_libname_gspphot'),
            #db.Gaia_DR3.ra_dec_corr.alias('gaia_ra_dec_corr'),
            #db.Gaia_DR3.ra_parallax_corr.alias('gaia_ra_parallax_corr'),
            #db.Gaia_DR3.ra_pmra_corr.alias('gaia_ra_pmra_corr'),
            #db.Gaia_DR3.ra_pmdec_corr.alias('gaia_ra_pmdec_corr'),
            #db.Gaia_DR3.dec_parallax_corr.alias('gaia_dec_parallax_corr'),
            #db.Gaia_DR3.dec_pmra_corr.alias('gaia_dec_pmra_corr'),
            #db.Gaia_DR3.dec_pmdec_corr.alias('gaia_dec_pmdec_corr'),
            #db.Gaia_DR3.parallax_pmra_corr.alias('gaia_parallax_pmra_corr'),
            #db.Gaia_DR3.parallax_pmdec_corr.alias('gaia_parallax_pmdec_corr'),
            #db.Gaia_DR3.pmra_pmdec_corr.alias('gaia_pmra_pmdec_corr'),
            #db.Gaia_DR3.astrometric_n_obs_al.alias('gaia_astrometric_n_obs_al'),
            #db.Gaia_DR3.astrometric_n_obs_ac.alias('gaia_astrometric_n_obs_ac'),
            #db.Gaia_DR3.astrometric_n_good_obs_al.alias('gaia_astrometric_n_good_obs_al'),
            #db.Gaia_DR3.astrometric_n_bad_obs_al.alias('gaia_astrometric_n_bad_obs_al'),
            #db.Gaia_DR3.astrometric_gof_al.alias('gaia_astrometric_gof_al'),
            #db.Gaia_DR3.astrometric_chi2_al.alias('gaia_astrometric_chi2_al'),
            #db.Gaia_DR3.astrometric_excess_noise.alias('gaia_astrometric_excess_noise'),
            #db.Gaia_DR3.astrometric_excess_noise_sig.alias('gaia_astrometric_excess_noise_sig'),
            #db.Gaia_DR3.astrometric_params_solved.alias('gaia_astrometric_params_solved'),
            #db.Gaia_DR3.astrometric_primary_flag.alias('gaia_astrometric_primary_flag'),
            #db.Gaia_DR3.nu_eff_used_in_astrometry.alias('gaia_nu_eff_used_in_astrometry'),
            #db.Gaia_DR3.pseudocolour.alias('gaia_pseudocolour'),
            #db.Gaia_DR3.pseudocolour_error.alias('gaia_pseudocolour_error'),
            #db.Gaia_DR3.ra_pseudocolour_corr.alias('gaia_ra_pseudocolour_corr'),
            #db.Gaia_DR3.dec_pseudocolour_corr.alias('gaia_dec_pseudocolour_corr'),
            #db.Gaia_DR3.parallax_pseudocolour_corr.alias('gaia_parallax_pseudocolour_corr'),
            #db.Gaia_DR3.pmra_pseudocolour_corr.alias('gaia_pmra_pseudocolour_corr'),
            #db.Gaia_DR3.pmdec_pseudocolour_corr.alias('gaia_pmdec_pseudocolour_corr'),
            #db.Gaia_DR3.astrometric_matched_transits.alias('gaia_astrometric_matched_transits'),
            #db.Gaia_DR3.visibility_periods_used.alias('gaia_visibility_periods_used'),
            #db.Gaia_DR3.astrometric_sigma5d_max.alias('gaia_astrometric_sigma5d_max'),
            #db.Gaia_DR3.matched_transits.alias('gaia_matched_transits'),
            #db.Gaia_DR3.new_matched_transits.alias('gaia_new_matched_transits'),
            #db.Gaia_DR3.matched_transits_removed.alias('gaia_matched_transits_removed'),
            #db.Gaia_DR3.ipd_gof_harmonic_amplitude.alias('gaia_ipd_gof_harmonic_amplitude'),
            #db.Gaia_DR3.ipd_gof_harmonic_phase.alias('gaia_ipd_gof_harmonic_phase'),
            #db.Gaia_DR3.ipd_frac_multi_peak.alias('gaia_ipd_frac_multi_peak'),
            #db.Gaia_DR3.ipd_frac_odd_win.alias('gaia_ipd_frac_odd_win'),
            #db.Gaia_DR3.scan_direction_strength_k1.alias('gaia_scan_direction_strength_k1'),
            #db.Gaia_DR3.scan_direction_strength_k2.alias('gaia_scan_direction_strength_k2'),
            #db.Gaia_DR3.scan_direction_strength_k3.alias('gaia_scan_direction_strength_k3'),
            #db.Gaia_DR3.scan_direction_strength_k4.alias('gaia_scan_direction_strength_k4'),
            #db.Gaia_DR3.scan_direction_mean_k1.alias('gaia_scan_direction_mean_k1'),
            #db.Gaia_DR3.scan_direction_mean_k2.alias('gaia_scan_direction_mean_k2'),
            #db.Gaia_DR3.scan_direction_mean_k3.alias('gaia_scan_direction_mean_k3'),
            #db.Gaia_DR3.scan_direction_mean_k4.alias('gaia_scan_direction_mean_k4'),

            #db.Gaia_DR3.phot_g_n_obs.alias('gaia_phot_g_n_obs'),
            #db.Gaia_DR3.phot_g_mean_flux.alias('gaia_phot_g_mean_flux'),
            #db.Gaia_DR3.phot_g_mean_flux_error.alias('gaia_phot_g_mean_flux_error'),
            #db.Gaia_DR3.phot_g_mean_flux_over_error.alias('gaia_phot_g_mean_flux_over_error'),
            #db.Gaia_DR3.phot_bp_n_obs.alias('gaia_phot_bp_n_obs'),
            #db.Gaia_DR3.phot_bp_mean_flux.alias('gaia_phot_bp_mean_flux'),
            #db.Gaia_DR3.phot_bp_mean_flux_error.alias('gaia_phot_bp_mean_flux_error'),
            #db.Gaia_DR3.phot_bp_mean_flux_over_error.alias('gaia_phot_bp_mean_flux_over_error'),

            #db.Gaia_DR3.phot_rp_n_obs.alias('gaia_phot_rp_n_obs'),
            #db.Gaia_DR3.phot_rp_mean_flux.alias('gaia_phot_rp_mean_flux'),
            #db.Gaia_DR3.phot_rp_mean_flux_error.alias('gaia_phot_rp_mean_flux_error'),
            #db.Gaia_DR3.phot_rp_mean_flux_over_error.alias('gaia_phot_rp_mean_flux_over_error'),
            #db.Gaia_DR3.phot_bp_n_contaminated_transits.alias('gaia_phot_bp_n_contaminated_transits'),
            #db.Gaia_DR3.phot_bp_n_blended_transits.alias('gaia_phot_bp_n_blended_transits'),
            #db.Gaia_DR3.phot_rp_n_contaminated_transits.alias('gaia_phot_rp_n_contaminated_transits'),
            #db.Gaia_DR3.phot_rp_n_blended_transits.alias('gaia_phot_rp_n_blended_transits'),
            #db.Gaia_DR3.phot_proc_mode.alias('gaia_phot_proc_mode'),
            #db.Gaia_DR3.bp_rp.alias('gaia_bp_rp'),
            #db.Gaia_DR3.bp_g.alias('gaia_bp_g'),
            #db.Gaia_DR3.g_rp.alias('gaia_g_rp'),
            db.TwoMassPSC.designation.alias('twomass_designation'),
            db.TwoMassPSC.j_m.alias('twomass_j_m'),
            db.TwoMassPSC.j_cmsig.alias('twomass_j_cmsig'),
            db.TwoMassPSC.j_msigcom.alias('twomass_j_msigcom'),
            db.TwoMassPSC.j_snr.alias('twomass_j_snr'),
            db.TwoMassPSC.h_m.alias('twomass_h_m'),
            db.TwoMassPSC.h_cmsig.alias('twomass_h_cmsig'),
            db.TwoMassPSC.h_msigcom.alias('twomass_h_msigcom'),
            db.TwoMassPSC.h_snr.alias('twomass_h_snr'),
            db.TwoMassPSC.k_m.alias('twomass_k_m'),
            db.TwoMassPSC.k_cmsig.alias('twomass_k_cmsig'),
            db.TwoMassPSC.k_msigcom.alias('twomass_k_msigcom'),
            db.TwoMassPSC.k_snr.alias('twomass_k_snr'),
            db.TwoMassPSC.ph_qual.alias('twomass_ph_qual'),
            db.TwoMassPSC.rd_flg.alias('twomass_rd_flg'),
            db.TwoMassPSC.bl_flg.alias('twomass_bl_flg'),
            db.TwoMassPSC.cc_flg.alias('twomass_cc_flg'),
            #db.TwoMassPSC.ndet.alias('twomass_ndet'),
            #db.TwoMassPSC.prox.alias('twomass_prox'),
            #db.TwoMassPSC.pxpa.alias('twomass_pxpa'),
            #db.TwoMassPSC.pxcntr.alias('twomass_pxcntr'),
            #db.TwoMassPSC.gal_contam.alias('twomass_gal_contam'),
            #db.TwoMassPSC.mp_flg.alias('twomass_mp_flg'),
            #db.TwoMassPSC.scan.alias('twomass_scan'),
            #db.TwoMassPSC.glon.alias('twomass_glon'),
            #db.TwoMassPSC.glat.alias('twomass_glat'),
            #db.TwoMassPSC.x_scan.alias('twomass_x_scan'),
            #db.TwoMassPSC.jdate.alias('twomass_jdate'),
            #db.TwoMassPSC.j_psfchi.alias('twomass_j_psfchi'),
            #db.TwoMassPSC.h_psfchi.alias('twomass_h_psfchi'),
            #db.TwoMassPSC.k_psfchi.alias('twomass_k_psfchi'),
            #db.TwoMassPSC.j_m_stdap.alias('twomass_j_m_stdap'),
            #db.TwoMassPSC.j_msig_stdap.alias('twomass_j_msig_stdap'),
            #db.TwoMassPSC.h_m_stdap.alias('twomass_h_m_stdap'),
            #db.TwoMassPSC.h_msig_stdap.alias('twomass_h_msig_stdap'),
            #db.TwoMassPSC.k_m_stdap.alias('twomass_k_m_stdap'),
            #db.TwoMassPSC.k_msig_stdap.alias('twomass_k_msig_stdap'),
            #db.TwoMassPSC.dist_edge_ns.alias('twomass_dist_edge_ns'),
            #db.TwoMassPSC.dist_edge_ew.alias('twomass_dist_edge_ew'),
            #db.TwoMassPSC.dist_edge_flg.alias('twomass_dist_edge_flg'),
            #db.TwoMassPSC.dup_src.alias('twomass_dup_src'),
            #db.TwoMassPSC.use_src.alias('twomass_use_src'),
            #db.TwoMassPSC.a.alias('twomass_a'),
            #db.TwoMassPSC.dist_opt.alias('twomass_dist_opt'),
            #db.TwoMassPSC.phi_opt.alias('twomass_phi_opt'),
            #db.TwoMassPSC.b_m_opt.alias('twomass_b_m_opt'),
            #db.TwoMassPSC.vr_m_opt.alias('twomass_vr_m_opt'),
            #db.TwoMassPSC.nopt_mchs.alias('twomass_nopt_mchs'),
            #db.TwoMassPSC.ext_key.alias('twomass_ext_key'),
            #db.TwoMassPSC.scan_key.alias('twomass_scan_key'),
            #db.TwoMassPSC.coadd_key.alias('twomass_coadd_key'),
            #db.TwoMassPSC.coadd.alias('twomass_coadd')
        )
        .distinct(db.SDSS_ID_To_Catalog.sdss_id)
        .join(db.Gaia_DR3, join_type=JOIN.LEFT_OUTER, on=(db.Gaia_DR3.source_id == db.SDSS_ID_To_Catalog.gaia_dr3_source))
        .switch(db.SDSS_ID_To_Catalog)
        .join(db.TwoMassPSC, join_type=JOIN.LEFT_OUTER, on=(db.TwoMassPSC.pts_key == db.SDSS_ID_To_Catalog.twomass_psc))
        .where(db.SDSS_ID_To_Catalog.sdss_id.in_(tuple(batch)))
        .dicts()
    )
    return list(q)


def query_catalog(sdss_ids: List[int], batch_size: int = 100, max_workers: int = 64):
    """
    Query the SDSS database for photometry and astrometry.

    Parameters
    ----------
    sdss_ids : List[int]
        List of SDSS IDs to query
    batch_size : int, optional
        Number of IDs per batch (default: 50000)
    max_workers : int, optional
        Number of parallel workers (default: 8). Set to 1 for sequential execution.

    Yields
    ------
    dict
        Dictionary containing catalog data for each SDSS ID
    """
    sdss_ids = sorted(list(set(sdss_ids).difference({0, -1})))

    batches = list(batched(sdss_ids, batch_size))

    if max_workers == 1:
        # Sequential execution
        for batch in batches:
            yield from _query_single_batch(batch)
    else:
        # Parallel execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_query_single_batch, batch) for batch in batches]
            for future in futures:
                yield from future.result()


def _query_gaia(source_ids):
    from almanac.database import catalogdb as db

    q = (
        db
        .Gaia_DR3
        .select(
            db.Gaia_DR3.source_id.alias('gaia_source_id'),
            db.Gaia_DR3.solution_id.alias('gaia_solution_id'),
            db.Gaia_DR3.ra.alias('gaia_ra'),
            db.Gaia_DR3.ra_error.alias('gaia_ra_error'),
            db.Gaia_DR3.dec.alias('gaia_dec'),
            db.Gaia_DR3.dec_error.alias('gaia_dec_error'),
            db.Gaia_DR3.parallax.alias('gaia_parallax'),
            db.Gaia_DR3.parallax_error.alias('gaia_parallax_error'),
            db.Gaia_DR3.pm.alias('gaia_pm'),
            db.Gaia_DR3.pmra.alias('gaia_pmra'),
            db.Gaia_DR3.pmra_error.alias('gaia_pmra_error'),
            db.Gaia_DR3.pmdec.alias('gaia_pmdec'),
            db.Gaia_DR3.pmdec_error.alias('gaia_pmdec_error'),
            db.Gaia_DR3.ruwe.alias('gaia_ruwe'),
            db.Gaia_DR3.duplicated_source.alias('gaia_duplicated_source'),
            db.Gaia_DR3.phot_g_mean_mag.alias('gaia_phot_g_mean_mag'),
            db.Gaia_DR3.phot_bp_mean_mag.alias('gaia_phot_bp_mean_mag'),
            db.Gaia_DR3.phot_rp_mean_mag.alias('gaia_phot_rp_mean_mag'),
            db.Gaia_DR3.phot_bp_rp_excess_factor.alias('gaia_phot_bp_rp_excess_factor'),
            db.Gaia_DR3.radial_velocity.alias('gaia_radial_velocity'),
            db.Gaia_DR3.radial_velocity_error.alias('gaia_radial_velocity_error'),
            db.Gaia_DR3.rv_nb_transits.alias('gaia_rv_nb_transits'),
            #db.Gaia_DR3.rv_method_used.alias('gaia_rv_method_used'),
            #db.Gaia_DR3.rv_nb_deblended_transits.alias('gaia_rv_nb_deblended_transits'),
            #db.Gaia_DR3.rv_visibility_periods_used.alias('gaia_rv_visibility_periods_used'),
            #db.Gaia_DR3.rv_expected_sig_to_noise.alias('gaia_rv_expected_sig_to_noise'),
            #db.Gaia_DR3.rv_renormalised_gof.alias('gaia_rv_renormalised_gof'),
            #db.Gaia_DR3.rv_chisq_pvalue.alias('gaia_rv_chisq_pvalue'),
            #db.Gaia_DR3.rv_time_duration.alias('gaia_rv_time_duration'),
            #db.Gaia_DR3.rv_amplitude_robust.alias('gaia_rv_amplitude_robust'),
            db.Gaia_DR3.rv_template_teff.alias('gaia_rv_template_teff'),
            db.Gaia_DR3.rv_template_logg.alias('gaia_rv_template_logg'),
            db.Gaia_DR3.rv_template_fe_h.alias('gaia_rv_template_fe_h'),
            db.Gaia_DR3.rv_atm_param_origin.alias('gaia_rv_atm_param_origin'),
            db.Gaia_DR3.vbroad.alias('gaia_vbroad'),
            db.Gaia_DR3.vbroad_error.alias('gaia_vbroad_error'),
            db.Gaia_DR3.vbroad_nb_transits.alias('gaia_vbroad_nb_transits'),
            db.Gaia_DR3.grvs_mag.alias('gaia_grvs_mag'),
            db.Gaia_DR3.grvs_mag_error.alias('gaia_grvs_mag_error'),
            db.Gaia_DR3.grvs_mag_nb_transits.alias('gaia_grvs_mag_nb_transits'),
            db.Gaia_DR3.rvs_spec_sig_to_noise.alias('gaia_rvs_spec_sig_to_noise'),
            db.Gaia_DR3.phot_variable_flag.alias('gaia_phot_variable_flag'),
            #db.Gaia_DR3.l.alias('gaia_l'),
            #db.Gaia_DR3.b.alias('gaia_b'),
            #db.Gaia_DR3.ecl_lon.alias('gaia_ecl_lon'),
            #db.Gaia_DR3.ecl_lat.alias('gaia_ecl_lat'),
            #db.Gaia_DR3.in_qso_candidates.alias('gaia_in_qso_candidates'),
            #db.Gaia_DR3.in_galaxy_candidates.alias('gaia_in_galaxy_candidates'),
            #db.Gaia_DR3.non_single_star.alias('gaia_non_single_star'),
            #db.Gaia_DR3.has_xp_continuous.alias('gaia_has_xp_continuous'),
            #db.Gaia_DR3.has_xp_sampled.alias('gaia_has_xp_sampled'),
            #db.Gaia_DR3.has_rvs.alias('gaia_has_rvs'),
            #db.Gaia_DR3.has_epoch_photometry.alias('gaia_has_epoch_photometry'),
            #db.Gaia_DR3.has_epoch_rv.alias('gaia_has_epoch_rv'),
            #db.Gaia_DR3.has_mcmc_gspphot.alias('gaia_has_mcmc_gspphot'),
            #db.Gaia_DR3.has_mcmc_msc.alias('gaia_has_mcmc_msc'),
            #db.Gaia_DR3.in_andromeda_survey.alias('gaia_in_andromeda_survey'),
            #db.Gaia_DR3.classprob_dsc_combmod_quasar.alias('gaia_classprob_dsc_combmod_quasar'),
            #db.Gaia_DR3.classprob_dsc_combmod_galaxy.alias('gaia_classprob_dsc_combmod_galaxy'),
            #db.Gaia_DR3.classprob_dsc_combmod_star.alias('gaia_classprob_dsc_combmod_star'),
            db.Gaia_DR3.teff_gspphot.alias('gaia_teff_gspphot'),
            #db.Gaia_DR3.teff_gspphot_lower.alias('gaia_teff_gspphot_lower'),
            #db.Gaia_DR3.teff_gspphot_upper.alias('gaia_teff_gspphot_upper'),
            db.Gaia_DR3.logg_gspphot.alias('gaia_logg_gspphot'),
            #db.Gaia_DR3.logg_gspphot_lower.alias('gaia_logg_gspphot_lower'),
            #db.Gaia_DR3.logg_gspphot_upper.alias('gaia_logg_gspphot_upper'),
            db.Gaia_DR3.mh_gspphot.alias('gaia_mh_gspphot'),
            #db.Gaia_DR3.mh_gspphot_lower.alias('gaia_mh_gspphot_lower'),
            #db.Gaia_DR3.mh_gspphot_upper.alias('gaia_mh_gspphot_upper'),
            db.Gaia_DR3.distance_gspphot.alias('gaia_distance_gspphot'),
            #db.Gaia_DR3.distance_gspphot_lower.alias('gaia_distance_gspphot_lower'),
            #db.Gaia_DR3.distance_gspphot_upper.alias('gaia_distance_gspphot_upper'),
            db.Gaia_DR3.azero_gspphot.alias('gaia_azero_gspphot'),
            #db.Gaia_DR3.azero_gspphot_lower.alias('gaia_azero_gspphot_lower'),
            #db.Gaia_DR3.azero_gspphot_upper.alias('gaia_azero_gspphot_upper'),
            db.Gaia_DR3.ag_gspphot.alias('gaia_ag_gspphot'),
        )
        .where(db.Gaia_DR3.source_id.in_(tuple(source_ids)))
        .dicts()
    )
    return list(q)

def _query_twomass(batch):
    from almanac.database import catalogdb as db

    q = (
        db
        .TwoMassPSC
        .select(
            db.TwoMassPSC.pts_key.alias('twomass_psc'),
            db.TwoMassPSC.designation.alias('twomass_designation'),
            db.TwoMassPSC.j_m.alias('twomass_j_m'),
            db.TwoMassPSC.j_cmsig.alias('twomass_j_cmsig'),
            db.TwoMassPSC.j_msigcom.alias('twomass_j_msigcom'),
            db.TwoMassPSC.j_snr.alias('twomass_j_snr'),
            db.TwoMassPSC.h_m.alias('twomass_h_m'),
            db.TwoMassPSC.h_cmsig.alias('twomass_h_cmsig'),
            db.TwoMassPSC.h_msigcom.alias('twomass_h_msigcom'),
            db.TwoMassPSC.h_snr.alias('twomass_h_snr'),
            db.TwoMassPSC.k_m.alias('twomass_k_m'),
            db.TwoMassPSC.k_cmsig.alias('twomass_k_cmsig'),
            db.TwoMassPSC.k_msigcom.alias('twomass_k_msigcom'),
            db.TwoMassPSC.k_snr.alias('twomass_k_snr'),
            db.TwoMassPSC.ph_qual.alias('twomass_ph_qual'),
            db.TwoMassPSC.rd_flg.alias('twomass_rd_flg'),
            db.TwoMassPSC.bl_flg.alias('twomass_bl_flg'),
            db.TwoMassPSC.cc_flg.alias('twomass_cc_flg'),
        )
        .where(db.TwoMassPSC.pts_key.in_(tuple(batch)))
        .dicts()
    )
    return list(q)


def _query_parallel(f, identifiers:  List[int], batch_size: int = 100, max_workers: int = 64):
    batches = batched(list(set(identifiers)), batch_size)

    if max_workers == 1:
        # Sequential execution
        for batch in batches:
            yield from f(batch)
    else:
        # Parallel execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(f, batch) for batch in batches]
            for future in concurrent.futures.as_completed(futures):
                yield from future.result()


def query_gaia(source_ids: List[int], batch_size: int = 100, max_workers: int = 64):
    """
    Query the SDSS database for Gaia DR3 data.

    Parameters
    ----------
    source_ids : List[int]
        List of Gaia source IDs to query
    batch_size : int, optional
        Number of IDs per batch (default: 50000)
    max_workers : int, optional
        Number of parallel workers (default: 8). Set to 1 for sequential execution.

    Yields
    ------
    dict
        Dictionary containing Gaia DR3 data for each source ID
    """
    yield from _query_parallel(_query_gaia, source_ids, batch_size=batch_size, max_workers=max_workers)


def query_twomass(twomass_pscs: List[int], batch_size: int = 100, max_workers: int = 64):
    """
    Query the SDSS database for TWOMASS PSC data.

    Parameters
    ----------
    twomass_pscs : List[int]
        List of Gaia source IDs to query
    batch_size : int, optional
        Number of IDs per batch (default: 50000)
    max_workers : int, optional
        Number of parallel workers (default: 8). Set to 1 for sequential execution.

    Yields
    ------
    dict
        Dictionary containing Gaia DR3 data for each source ID
    """
    yield from _query_parallel(_query_twomass, twomass_pscs, batch_size=batch_size, max_workers=max_workers)




def _query_identifiers(batch):
    """Query a single batch of SDSS IDs. Helper for parallelization."""
    from almanac.database import catalogdb as db

    q = (
        db
        .SDSS_ID_To_Catalog
        .select(
            db.SDSS_ID_To_Catalog.sdss_id,
            db.SDSS_ID_To_Catalog.catalogid,
            db.SDSS_ID_To_Catalog.version_id,
            db.SDSS_ID_To_Catalog.lead,
            db.SDSS_ID_To_Catalog.allstar_dr17_synspec_rev1,
            db.SDSS_ID_To_Catalog.allwise,
            db.SDSS_ID_To_Catalog.bhm_rm_v0,
            db.SDSS_ID_To_Catalog.bhm_rm_v0_2,
            db.SDSS_ID_To_Catalog.catwise,
            db.SDSS_ID_To_Catalog.catwise2020,
            db.SDSS_ID_To_Catalog.gaia_dr2_source,
            db.SDSS_ID_To_Catalog.gaia_dr3_source,
            db.SDSS_ID_To_Catalog.glimpse,
            db.SDSS_ID_To_Catalog.guvcat,
            db.SDSS_ID_To_Catalog.legacy_survey_dr10,
            db.SDSS_ID_To_Catalog.legacy_survey_dr8,
            db.SDSS_ID_To_Catalog.mangatarget,
            db.SDSS_ID_To_Catalog.marvels_dr11_star,
            db.SDSS_ID_To_Catalog.marvels_dr12_star,
            db.SDSS_ID_To_Catalog.mastar_goodstars,
            db.SDSS_ID_To_Catalog.panstarrs1,
            db.SDSS_ID_To_Catalog.ps1_g18,
            db.SDSS_ID_To_Catalog.sdss_dr13_photoobj,
            db.SDSS_ID_To_Catalog.sdss_dr17_specobj,
            db.SDSS_ID_To_Catalog.skymapper_dr1_1,
            db.SDSS_ID_To_Catalog.skymapper_dr2,
            db.SDSS_ID_To_Catalog.supercosmos,
            db.SDSS_ID_To_Catalog.tic_v8,
            db.SDSS_ID_To_Catalog.twomass_psc,
            db.SDSS_ID_To_Catalog.tycho2,
            db.SDSS_ID_To_Catalog.unwise,
        )
        .where(db.SDSS_ID_To_Catalog.sdss_id.in_(tuple(batch)))
        .dicts()
    )
    return list(q.iterator())



def query_identifiers(sdss_ids: List[int], batch_size: int = 100, max_workers: int = 32):
    """
    Query the SDSS database for photometry and astrometry.

    Parameters
    ----------
    sdss_ids : List[int]
        List of SDSS IDs to query
    batch_size : int, optional
        Number of IDs per batch (default: 50000)
    max_workers : int, optional
        Number of parallel workers (default: 8). Set to 1 for sequential execution.

    Yields
    ------
    dict
        Dictionary containing catalog data for each SDSS ID
    """
    yield from _query_parallel(_query_identifiers, sdss_ids, batch_size, max_workers)
