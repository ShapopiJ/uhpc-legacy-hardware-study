#!/bin/sh
#PBS -N MRG_Cen_A_ModelPlus_HESSI_Stereo_Faint_Cen_A_Dot_list

module load singularity/3.11
unset HPSS
unset XROOTD
export NOHPSS="1"
export NOXROOTD="1"
export ROOTSYS="/home/software/root/root-6.24.06/install"
export HESSROOT="/home/software/hess/ParisAnalysis/pa-chain-paris-0-10-0-branch_root6"
export PATH="/home/software/hess/ParisAnalysis/pa-chain-paris-0-10-0-branch_root6/scons/local:/home/software/root/root-6.24.06/astro_root-4.1.2/bin:/home/software/hess/ParisAnalysis/pa-chain-paris-0-10-0-branch_root6/scons/local:/home/software/hess/ParisAnalysis/pa-chain-paris-0-10-0-branch_root6/bin:/home/software/root/root-6.24.06/install/bin:/home/software/hess/anaconda3/envs/py37/bin:/home/software/git/git-2.9.4/install/bin:/home/software/go/1.22.4/gopath/src/github.com/sylabs/singularity-3.11/install/bin:/home/software/go/1.22.4/go/bin:/home/software/gcc/gcc11/install/bin:/home/jshapopi/DAQ/git-subrepo/lib:/home/software/hess/anaconda3/v2025.06/condabin:/home/jshapopi/.local/bin:/opt/ohpc/pub/utils/prun/1.2:/opt/ohpc/pub/utils/autotools/bin:/opt/ohpc/pub/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/opt/pbs/bin"
export LD_LIBRARY_PATH="/home/software/hess/ParisAnalysis/pa-chain-paris-0-10-0-branch_root6/lib:/home/software/root/root-6.24.06/install/lib:/home/software/gcc/gcc11/install/lib64"
export PYTHONPATH="/home/software/hess/ParisAnalysis/pa-chain-paris-0-10-0-branch_root6/:/home/software/root/root-6.24.06/install/lib"
module load singularity/3.11
export SINGULARITYCMD="unam-root"
export TMPBATCH="/home/jshapopi"

export JOBTMPDIR="`mktemp -t -d merge_Cen_A_ModelPlus_HESSI_Stereo_Faint_Cen_A_Dot_list.XXXX`"
cd $JOBTMPDIR

cat > rootlogon.C  << EOF
{
// Analysis
gSystem->Load("librootparisanalysis.so");
gSystem->Load("librootparisanalysis_scripts.so");
gSystem->Load("librootparisanalysisCommon_scripts.so");
// DST
// Model++ DST
gSystem->Load("libHessModelStorage.so");
gSystem->Load("libHessModelGen.so");
gSystem->Load("libHessModelUtil.so");
// Reconstruction
// Model++
gSystem->Load("librootparisanalysisModel.so");
gSystem->Load("librootparisanalysisModel_scripts.so");
}
EOF
rsync -avP /home/jshapopi/Tests/./Results_Cen_A_ModelPlus_HESSI_Stereo_Faint_Cen_A_Dot_list_slice_*.root ./
rsync -avP /home/jshapopi/Tests/./EventsList_Cen_A_ModelPlus_HESSI_Stereo_Faint_Cen_A_Dot_list_slice_*.root ./
cat > merge_Cen_A_ModelPlus_HESSI_Stereo_Faint_Cen_A_Dot_list.C  << EOF
void merge_Cen_A_ModelPlus_HESSI_Stereo_Faint_Cen_A_Dot_list()
{
if(gROOT->IsBatch())
gROOT->SetStyle("Plain");
gStyle->SetOptFit(111);
gStyle->SetPalette(1);
//===================
// = Path 
set_verbose(true);
generate_stacktrace(false);
//===================
// = Substractions = 
set_histotheta2max(0.1);
set_histotheta2nbins(60);
use_ring_background(true);
use_full_background(false);
use_gamma_fov_storage(false,false);
use_multipleoff_background(true);
multipleoff_background_optimize_regions(false);
multipleoff_background_normalizefullhisto(false);
multipleoff_background_exclude_onoff(true);
multipleoff_set_n_offregions(-1);
multipleoff_use_acceptance_gradient(true);
use_onoff_background(false);
//===================
// = Maps = 
set_mapextension(2,2);
set_mapbinsize(0.02);
set_oversampling_size(0.1);
generate_acceptance_model(true);
generate_sky_acceptance(true);
set_acceptance_type(ParisAnalysis::AcceptanceInfo::Acceptance_TwoD);
use_zenithdependant_acceptance(true);
use_ring_backgroundmap(true,true,true);
use_adaptivering_backgroundmap(false);
use_template_background(true);
use_sandwich_backgroundmap(false);
use_onoff_backgroundmap(false);
use_acceptance_gradient_correction(true);
set_gradient_correction_max_angle(2);
set_gradient_correction_max_gradient(0.1);
set_purge_merging_files(0);
merge_slices("Cen_A_ModelPlus_HESSI_Stereo_Faint_Cen_A_Dot_list",true,false,0.100000);
merge_slices_tuples("Cen_A_ModelPlus_HESSI_Stereo_Faint_Cen_A_Dot_list");
gApplication->Terminate(0);
}
EOF
$SINGULARITYCMD root -b 'merge_Cen_A_ModelPlus_HESSI_Stereo_Faint_Cen_A_Dot_list.C'
mkdir -p /home/jshapopi/Tests/.
cp -v ./Results_Cen_A_ModelPlus_HESSI_Stereo_Faint_Cen_A_Dot_list_merged.root /home/jshapopi/Tests/./Results_Cen_A_ModelPlus_HESSI_Stereo_Faint_Cen_A_Dot_list_merged.root
mkdir -p /home/jshapopi/Tests/.
cp -v ./EventsList_Cen_A_ModelPlus_HESSI_Stereo_Faint_Cen_A_Dot_list_merged.root /home/jshapopi/Tests/./EventsList_Cen_A_ModelPlus_HESSI_Stereo_Faint_Cen_A_Dot_list_merged.root
