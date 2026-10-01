#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <android-base/properties.h>

#define _REALLY_INCLUDE_SYS__SYSTEM_PROPERTIES_H_
#include <sys/_system_properties.h>

using android::base::GetProperty;
using std::string;

void property_override(string prop, string value)
{
    auto pi = (prop_info *)__system_property_find(prop.c_str());

    if (pi != nullptr)
        __system_property_update(pi, value.c_str(), value.size());
    else
        __system_property_add(prop.c_str(), prop.size(), value.c_str(), value.size());
}

void vendor_load_properties()
{
    const string prop_partitions[] = {"", "bootimage.", "odm.", "odm_dlkm.", "product.", "system.", "system_ext.", "vendor.", "vendor_dlkm."};
    for (const string &prop : prop_partitions)
    {
        property_override(string("ro.product.") + prop + string("name"), "X6871-OP");
        property_override(string("ro.product.") + prop + string("marketname"), "Infinix GT 20 Pro");
        property_override(string("ro.product.") + prop + string("model"), "Infinix X6871");
        property_override(string("ro.product.") + prop + string("brand"), "Infinix");
        property_override(string("ro.product.") + prop + string("manufacturer"), "INFINIX");
        property_override(string("ro.product.") + prop + string("device"), "Infinix-X6871");
    }

    property_override("ro.build.product", "Infinix-X6871");
    property_override("ro.build.display.id", "X6871-15.1.2.180SP05(OP001PF001AZ)");
    property_override("ro.build.version.incremental", "180003");
    property_override("ro.build.fingerprint", "Infinix/X6871-OP/Infinix-X6871:16/BP2A.250605.031.A3/301550050:user/release-keys");
    property_override("ro.vendor.build.fingerprint", "Infinix/X6871-OP/Infinix-X6871:16/BP2A.250605.031.A3/301550050:user/release-keys");
    property_override("ro.system.build.fingerprint", "Infinix/X6871-OP/Infinix-X6871:16/BP2A.250605.031.A3/301550050:user/release-keys");
    property_override("ro.vendor.tran.vibrator.option", "single");
    property_override("ro.tran_vibrate_ontouch.support", "1");
    property_override("ro.tran_vibrate_ontouch2.0.support", "1");
    property_override("ro.vendor.mtk_thermal_2_0", "1");
    property_override("ro.vendor.thermalspace.support", "1");
}
