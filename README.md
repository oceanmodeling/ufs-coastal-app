# Introduction 
The ufs-coastal-app repository is the umbrella for the UFS Coastal project currently under development by NOAA and NCAR, which supports coastal forecast requirements. The UFS Coastal Application is meant to constitute a workflow for coastal forecasting, wherein the coupling infrastructure is provided by [this fork of  ufs-weather-model](https://github.com/oceanmodeling/ufs-weather-model), which is currently in active development.

The [model-level repo](https://github.com/oceanmodeling/ufs-weather-model) contains the model code and external links needed to build the Unified Forecast System (UFS) coastal model executable and associated model components, including the ROMS, FVCOM, ADCIRC and SCHISM plus WaveWatch III model components. 

Here, model component means a forecast component (e.g. coastal ocean model) that represents a physical domain (e.g. Atlantic Ocean) or process (e.g. biogeochemistry). An application is a workflow that is designed for a particular forecasting purpose. A workflow consists of a set of model components and coupling infrastructure, provided by UFS Coastal Model, pre- and post-processing scripts, and is associated with a range of valid coupling configurations. 

# Where to find more information 
* [Documentation](https://ufs-coastal-application.readthedocs.io/en/latest/index.html) (under construction!) 
* [UFS Coastal Wiki](https://github.com/oceanmodeling/ufs-weather-model/wiki/) (under construction!) 
* [UFS Coastal Discussions Board](https://github.com/oceanmodeling/ufs-weather-model/discussions)
* [UFS Community Discussions](https://github.com/orgs/ufs-community/discussions)
* [UFS Community Wiki](https://github.com/ufs-community/ufs/wiki)
* [Contributing code to the UFS (EPIC)](https://github.com/ufs-community/ufs/wiki)

# Supported model components
Model components currently supported on top of ufs-weather-model components are as follows. Each model component is provided as a submodule via forks of the authoritative model repos. UFS-related model component issues are handled within these forks:

[ADCIRC](https://github.com/oceanmodeling/adcirc)\
[SCHISM](https://github.com/oceanmodeling/schism)\
[WW3](https://github.com/oceanmodeling/WW3)\
[ROMS](https://github.com/oceanmodeling/roms)\
[FVCOM](https://github.com/oceanmodeling/FVCOM)

# Points of contact
Points of contact & repos for specific questions regarding each model component, as well as NOAA and NCAR project teams, are listed below. The authoritative model repositories are also linked below. 

[ADCIRC](https://github.com/adcirc/adcirc)\
Damrongsak Wirasaet (dwirasae@nd.edu)\
Joannes Westerink (jjw@nd.edu) 

[FVCOM](https://github.com/FVCOM-GitHub)\
Jianhua Qi (jqi@umassd.edu)\
Siqi Li (sli4@umassd.edu)\
Changsheng Chen (c1chen@umassd.edu)			

[PAHM](https://github.com/noaa-ocs-modeling/PaHM)\
Panagiotis Velissariou (panagiotis.velissariou@noaa.gov)

[ROMS](https://github.com/myroms/roms)\
Hernan G. Arango (arango@marine.rutgers.edu)

[SCHISM](https://github.com/schism-dev/schism)\
Y. Joseph Zhang (yjzhang@vims.edu)\
Carsten Lemmen (carsten.lemmen@hereon.de)

[WW3](https://github.com/NOAA-EMC/WW3)\
Saeideh Banihashemi (saeideh.banihashemi@noaa.gov)\
Ali Salimi (ali.salimi@noaa.gov)\
Ali Abdolali (Ali.Abdolali@erdc.dren.mil)

**NOAA NOS dev team**\
Saeed Moghimi (saeed.moghimi@noaa.gov)\
Mansur Jisan (mansur.jisan@noaa.gov)\
Yunfang Sun (yunfang.sun@noaa.gov)\
Jana Haddad (jana.haddad@noaa.gov)\

**NCAR dev team**\
Ufuk Turuncoglu (turuncu@ucar.edu)\
Daniel Rosen (drosen@ucar.edu)\
Ann Tsay (atsay@ucar.edu)					

# References
[1] Moghimi, S., Van der Westhuysen, A., Abdolali, A., Myers, E., Vinogradov, S., Ma, Z., Liu, F., Mehra, A., & Kurkowski, N. (2020). Development of an ESMF Based Flexible Coupling Application of ADCIRC and WAVEWATCH III for High Fidelity Coastal Inundation Studies. Journal of Marine Science and Engineering, 8(5), 308. https://doi.org/10.3390/jmse8050308

[2] Moghimi, S., Vinogradov, S., Myers, E. P., Funakoshi, Y., Van der Westhuysen, A. J., Abdolali, A., Ma, Z., & Liu, F. (2019). Development of a Flexible Coupling Interface for ADCIRC model for Coastal Inundation Studies. NOAA Technical Memorandum, NOS CS(41). https://repository.library.noaa.gov/view/noaa/20609/

[3] Moghimi, S., Westhuysen, A., Abdolali, A., Myers, E., Vinogradov, S., Ma, Z., Liu, F., Mehra, A., & Kurkowski, N. (2020). Development of a Flexible Coupling Framework for Coastal Inundation Studies. https://arxiv.org/abs/2003.12652

# Disclaimer
The United States Department of Commerce (DOC) GitHub project code is provided on an "as is" basis and the user assumes responsibility for its use. DOC has relinquished control of the information and no longer has responsibility to protect the integrity, confidentiality, or availability of the information. Any claims against the Department of Commerce stemming from the use of its GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.


