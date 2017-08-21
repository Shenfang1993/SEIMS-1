#include "ImplicitKinematicWave.h"
#include <map>
#include "api.h"

using namespace std;

extern "C" SEIMS_MODULE_API SimulationModule * GetInstance() {
    return new ImplicitKinematicWave_OL();
}

// function to return the XML Metadata document string
extern "C" SEIMS_MODULE_API const char *MetadataInformation() {
    string res = "";
    MetadataInfo mdi;

    // set the information properties
    mdi.SetAuthor("Junzhi Liu");
    mdi.SetClass(MCLS_OL_ROUTING, MCLSDESC_OL_ROUTING);
    mdi.SetDescription(MDESC_IKW_OL);
    mdi.SetEmail(SEIMS_EMAIL);
    mdi.SetHelpfile("IKW_OL.chm");
    mdi.SetID(MID_IKW_OL);
    mdi.SetName(MID_IKW_OL);
    mdi.SetVersion("0.1");
    mdi.SetWebsite(SEIMS_SITE);

	MetadataInfo::AddModuleMetadata<ImplicitKinematicWave_OL>(mdi);
    res = mdi.GetXMLDocument();

    char *tmp = new char[res.size() + 1];
    strprintf(tmp, res.size() + 1, "%s", res.c_str());
    return tmp;
}
//mdi.AddOutput("CELLH", "mm", "Water depth in the downslope boundary of cells", DT_Raster);