from pathlib import Path
from astropy import units as u
from astropy.coordinates import SkyCoord
from regions import CircleSkyRegion

# %matplotlib inline
import matplotlib.pyplot as plt
from IPython.display import display
from gammapy.data import DataStore
from gammapy.datasets import Datasets, MapDataset, MapDatasetOnOff
from gammapy.estimators import FluxPointsEstimator
from gammapy.makers import RingBackgroundMaker, MapDatasetMaker, SafeMaskMaker
from gammapy.maps import Map, MapAxis, WcsGeom
from gammapy.modeling import Fit
from gammapy.modeling.models import (
    FoVBackgroundModel,
    PointSpatialModel,
    PowerLawSpectralModel,
    SkyModel,
)
from gammapy.utils.check import check_tutorials_setup
from gammapy.visualization import plot_npred_signal
from gammapy.analysis import Analysis, AnalysisConfig
from gammapy.datasets import MapDatasetOnOff
from gammapy.estimators import ExcessMapEstimator
import matplotlib.pyplot as plt
from scipy.stats import norm
import numpy as np
import os


## PA
path_data = "/home/software/hess/data_temp/FITS/47_Tuc/Model_HESSII_Hybrid_Prod10_PreProd6/Model_HESSII_Hybrid_Prod10_PreProd6"

os.environ['HESS_FITS'] = path_data
analysis_configs = os.listdir(path_data)
conf = 'ModelPlus_HESS_Combined_Stereo_FaintHiRes'

path = os.path.join(path_data, conf)
datastore = DataStore.from_dir(path)

position = SkyCoord.from_name("47 Tucanae")
offset_max = 2.0 * u.deg
theta_cut = 0.1*u.deg

####################Remove cone search and just use the runlist##########################

config = AnalysisConfig()
config.observations.datastore = path
# We define the cone search parameters
config.observations.obs_cone.frame = "icrs"
config.observations.obs_cone.lon = position.icrs.ra
config.observations.obs_cone.lat = position.icrs.dec
config.observations.obs_cone.radius = "2.0 deg"

analysis = Analysis(config)
analysis.get_observations()

#datastore = DataStore.from_dir(path)
runs = ['29389', '29432', '29433', '29449', '29485', '29486', '29489', '29490', '29538', '29539',  '29632', '29658', '29659', '29660', '29680', '29681', '29682', '29683', '29684', '29691', '29692', '29693', '29703', '29704', '29705', '29706', '29707', '29729', '48981', '48982', '49001', '49002', '49003', '49023', '49024', '49042', '49062', '52589', '52710', '52724', '52725', '52845', '53650', '53651', '53677', '53705', '53731', '54142', '54143', '54173', '54174', '54175', '54176', '54177', '58926', '58975', '59018', '59090', '59091', '59102', '59126', '59418', '59444', '59474', '59475', '59500', '59501', '59530', '59531', '59552', '59575', '59576', '59593', '59594', '59650', '59651', '61401', '61411', '61493', '61783', '61790', '61791', '61801', '61802', '61803', '74312', '74358', '74359', '74404', '74406', '74454', '74455', '74456', '74505', '74507', '75091', '75092', '75458', '75462', '75494', '96323', '96374', '96443', '96471', '96472', '96510', '96511', '96573', '96605', '96606', '96661', '96662', '96663', '96716', '96718', '96776', '96777', '96876', '97177', '97178', '97211', '97212', '97213', '97257', '97258', '97259', '97260', '97261', '97304', '97352', '97353', '97361', '97408', '97409', '97410', '97411', '97412', '97413', '97414', '97454', '97455', '97456', '97457', '97458', '97459', '97460', '97487', '97488', '97489', '97490', '97491', '97492', '97493', '97509', '97510', '97511', '97512', '97513', '97514', '97561', '97593', '97595', '97596', '97597', '97618', '97619', '97620', '97621', '97640', '97641', '97643', '97644', '97645', '97646', '97647', '97648', '97688', '97689', '97706', '97708', '97709', '97722', '100044', '100087', '100088', '100166', '100167', '100169', '100214', '100217', '100249', '100250', '100251', '100289', '100290', '100317', '100318', '100319', '100344', '100347', '100379', '100381', '100413', '100438', '100439', '100440', '100467', '100468', '100471', '101009', '101029', '101030', '101062', '135172', '140245', '140274', '140275', '140276', '140311', '140312', '140426', '140428', '140429', '140465', '140466', '140498', '140499', '140500', '140527', '140528', '140529', '140552', '140553', '140554', '140555', '140619', '140620', '140621', '140623', '140636', '140637', '140638', '140639', '140640', '140658', '140659', '140660', '140677', '140987', '140988', '140989', '141019', '141050', '141052', '141083', '141084', '141173', '141224', '141268', '141271', '141272', '141273', '141274', '141275', '141306', '141307', '141308', '141309', '141310', '141331', '141332', '141333', '141346', '141347', '141360', '141361', '141362', '141363', '141364', '141373', '141374', '141375', '141376', '141386', '141394', '141599', '141629', '141630', '141631', '141692', '141693', '141782', '141784', '142850', '142851', '142852', '142868', '142891', '142950', '142951', '142952', '142954', '142955', '142980', '142981', '142982', '142983', '142984', '143034', '143035', '143036', '143064', '143065', '143066', '143067', '143068', '143093', '143094', '143095', '143096', '143097', '143098', '143120', '143121', '143122', '143149', '143150', '143151', '143200', '143201', '143202', '153896', '153957', '153958', '153961', '154005', '154006', '154119', '154120', '154166', '154167', '154168', '154215', '154217', '154218', '154267', '154268', '154269', '154294', '154295', '154296', '154297', '154298', '154356', '154362', '154401', '154651',  '154824', '154831', '154861', '154863', '154864', '154866', '154868', '154897', '154901', '155048', '155049', '155051', '155053', '155121', '155125', '155137', '155155', '155162', '155208', '155221', '155287']
runs = np.array(runs, dtype=int)
print(f'The actual number of runs I will analyze is: {len(runs)}')
#observations = datastore.get_observations(runs, skip_missing=True)
print('found {} runs: {}'.format(len(analysis.observations.ids), analysis.observations.ids))
print(f'Number of observations: {len(analysis.observations)}')

# Region and Map Geometry
from regions import CircleSkyRegion, RectangleSkyRegion
on_region = CircleSkyRegion(center=position, radius=theta_cut)

# minimum and maximum energy for the analysis
Emin =0.2*u.TeV
Emax = 30*u.TeV
# number of energy bins in the map
map_nEbins = 15
# width of the map
map_width = 8*u.deg
# bin size of the map
map_binsz = 0.01*u.deg

map_energy_axis = MapAxis.from_energy_bounds(Emin, Emax,
                                             nbin=map_nEbins, 
                                             name="energy")
#map_energy_axis_true = MapAxis.from_energy_bounds(0.1, 60, 30, unit='TeV', 
#                                             name="energy_true")

map_geom = WcsGeom.create(skydir=position,
                          axes=[map_energy_axis],
                          width=map_width,
                          binsz=map_binsz)

#name = "47Tuc"
#map_stacked = MapDataset.create(
#    geom=map_geom, energy_axis_true=map_energy_axis_true, name=name
#)
map_stacked = None

#Exclusion
posHS=SkyCoord(8.8,-71.9, unit="deg", frame="icrs")
regionHS = CircleSkyRegion(center=posHS, radius=0.2*u.deg)

circle = CircleSkyRegion(center=position, radius=0.3 * u.deg)
exclusion_regions = [circle, regionHS]
exclusion_mask = map_geom.to_image().region_mask(exclusion_regions, inside =False) 
exclusion_mask.plot()
plt.savefig("ExclusionMask.png")

#Build background model
map_empty = MapDataset.create(map_geom, name='empty')
map_maker = MapDatasetMaker(selection=["counts", "exposure", "edisp", "psf"])
safe_mask_maker = SafeMaskMaker(methods=["offset-max", "aeff-max"], 
                                offset_max=offset_max
                                ,aeff_percent=10
                               )
ring_bkg_maker = RingBackgroundMaker(exclusion_mask=exclusion_mask,
                                     r_in="0.9 deg", width="0.3 deg")


count = 1

failed_runs_maps = []

for obs_id, obs in zip(analysis.observations.ids, analysis.observations):
    if obs.obs_id not in runs:
        print(f'Skipping {obs.obs_id}: not in HAP runlist')
        continue
    print('[{}] {}/{}     '.format(obs.obs_id, count, len(analysis.observations.ids)), end = '\r')
    count += 1
  
    try :
        map_dataset = map_maker.run(map_empty.copy(name=str(obs_id)), obs)
        map_dataset = safe_mask_maker.run(map_dataset, obs)

        ## use the gamma acceptance as background acceptance
        ## I'm not really sure why we need two data sets. But otherwise the RingBackground does not produce good results.
        map_dataset2 = map_maker.run(map_empty.copy(name=str(obs_id)), obs)
        map_dataset2 = safe_mask_maker.run(map_dataset2, obs)
        map_dataset.background = map_empty.background
        map_dataset.background.data = map_dataset2.exposure.data

        map_dataset = ring_bkg_maker.run(map_dataset)

        if map_stacked is None :
            map_stacked = map_dataset.copy('stacked')
        else :
            map_stacked.stack(map_dataset)

        ## keep the map datasets
        #map_datasets.append(map_dataset)
        ## delete the individual maps to save memory
        del map_dataset
            
    except Exception as e:
        print('skipped {}'.format(obs_id))
        failed_runs_maps.append(obs_id)
        print(e)

map_stacked.write(conf + '_MapDataset_job.fits.gz', overwrite = True)



estimator = ExcessMapEstimator(theta_cut, selection_optional='')
fluxmaps = estimator.run(map_stacked)
significance_map = fluxmaps["sqrt_ts"]
excess_map = fluxmaps["npred_excess"]
plt.figure(figsize=(10, 10))
ax1 = plt.subplot(221, projection=significance_map.geom.wcs)
ax2 = plt.subplot(222, projection=excess_map.geom.wcs)
ax1.set_title("Significance map")
significance_map.plot(ax=ax1, add_cbar=True)
ax2.set_title("Excess map")
excess_map.plot(ax=ax2, add_cbar=True)
significance_map.write(conf + "_SigMap.fits", overwrite=True)
plt.savefig(conf + '_SigMap.png')
plt.clf()

###################################################Distribution####################################################################

significance_map_off = significance_map.get_image_by_idx([0]) * exclusion_mask
#significance_map_off = significance_map * exclusion_mask

significance_all = significance_map.data[np.isfinite(significance_map.data)]
significance_off = significance_map_off.data[
    np.isfinite(significance_map_off.data)
]

plt.hist(
    significance_all,
    density=True,
    alpha=0.5,
    color="red",
    label="all bins",
    histtype='step',
    
    bins=21,
)

plt.hist(
    significance_off,
    density=True,
    alpha=0.5,
    color="blue",
    label="off bins",
    histtype='step',
    
    bins=21,
)

# Now, fit the off distribution with a Gaussian
mu, std = norm.fit(significance_off)
x = np.linspace(-8, 8, 50)
p = norm.pdf(x, mu, std)
plt.plot(x, p, lw=2, color="black")
plt.legend()
plt.xlabel("Significance")
plt.yscale("log")
plt.ylim(1e-5, 1)
xmin, xmax = np.min(significance_all), np.max(significance_all)
plt.xlim(xmin, xmax+1)
ax = plt.gca()
ax.text(2, 0.9e-1, f'mean = {mu:.2f}, width = {std:.2f}', style='italic',
        bbox={})
plt.savefig(conf + '_SigDist.png')


print(f"Fit results: mu = {mu:.2f}, std = {std:.2f}")