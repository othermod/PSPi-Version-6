// pspi_battery.c - power_supply device driven from userspace by battery_monitor
#include <linux/module.h>
#include <linux/platform_device.h>
#include <linux/power_supply.h>

static int capacity   = 50;
static int status     = 0;       // 0=discharging, 1=charging, 2=charged
static int voltage_uv = 3800000;
static int current_ua;
static int online;

static struct power_supply *bat_psy, *ac_psy;

// Writing any parameter fires a uevent so udev/UPower refresh right away.
static int param_set_notify(const char *val, const struct kernel_param *kp)
{
    int ret = param_set_int(val, kp);
    if (ret)
        return ret;
    if (bat_psy)
        power_supply_changed(bat_psy);
    if (ac_psy)
        power_supply_changed(ac_psy);
    return 0;
}

static const struct kernel_param_ops notify_ops = {
    .set = param_set_notify,
    .get = param_get_int,
};

module_param_cb(capacity,   &notify_ops, &capacity,   0644);
module_param_cb(status,     &notify_ops, &status,     0644);
module_param_cb(voltage_uv, &notify_ops, &voltage_uv, 0644);
module_param_cb(current_ua, &notify_ops, &current_ua, 0644);
module_param_cb(online,     &notify_ops, &online,     0644);

static enum power_supply_property bat_props[] = {
    POWER_SUPPLY_PROP_STATUS,
    POWER_SUPPLY_PROP_PRESENT,
    POWER_SUPPLY_PROP_TECHNOLOGY,
    POWER_SUPPLY_PROP_CAPACITY,
    POWER_SUPPLY_PROP_VOLTAGE_NOW,
    POWER_SUPPLY_PROP_CURRENT_NOW,
    POWER_SUPPLY_PROP_SCOPE,
};

static enum power_supply_property ac_props[] = {
    POWER_SUPPLY_PROP_ONLINE,
};

static int bat_get_property(struct power_supply *psy,
                            enum power_supply_property psp,
                            union power_supply_propval *val)
{
    switch (psp) {
    case POWER_SUPPLY_PROP_STATUS:
        val->intval = (status == 2) ? POWER_SUPPLY_STATUS_FULL :
                      (status == 1) ? POWER_SUPPLY_STATUS_CHARGING :
                                      POWER_SUPPLY_STATUS_DISCHARGING;
        break;
    case POWER_SUPPLY_PROP_PRESENT:
        val->intval = 1;
        break;
    case POWER_SUPPLY_PROP_TECHNOLOGY:
        val->intval = POWER_SUPPLY_TECHNOLOGY_LION;
        break;
    case POWER_SUPPLY_PROP_CAPACITY:
        val->intval = capacity;
        break;
    case POWER_SUPPLY_PROP_VOLTAGE_NOW:
        val->intval = voltage_uv;
        break;
    case POWER_SUPPLY_PROP_CURRENT_NOW:
        val->intval = current_ua;
        break;
    case POWER_SUPPLY_PROP_SCOPE:
        val->intval = POWER_SUPPLY_SCOPE_SYSTEM;
        break;
    default:
        return -EINVAL;
    }
    return 0;
}

static int ac_get_property(struct power_supply *psy,
                           enum power_supply_property psp,
                           union power_supply_propval *val)
{
    if (psp != POWER_SUPPLY_PROP_ONLINE)
        return -EINVAL;
    val->intval = online;
    return 0;
}

static const struct power_supply_desc bat_desc = {
    .name           = "BAT0",
    .type           = POWER_SUPPLY_TYPE_BATTERY,
    .properties     = bat_props,
    .num_properties = ARRAY_SIZE(bat_props),
    .get_property   = bat_get_property,
};

static const struct power_supply_desc ac_desc = {
    .name           = "pspi-ac",
    .type           = POWER_SUPPLY_TYPE_MAINS,
    .properties     = ac_props,
    .num_properties = ARRAY_SIZE(ac_props),
    .get_property   = ac_get_property,
};

static struct platform_device *pdev;

static int __init pspi_battery_init(void)
{
    struct power_supply_config cfg = {};

    pdev = platform_device_register_simple("pspi-battery", -1, NULL, 0);
    if (IS_ERR(pdev))
        return PTR_ERR(pdev);

    bat_psy = power_supply_register(&pdev->dev, &bat_desc, &cfg);
    if (IS_ERR(bat_psy))
        goto err_bat;

    ac_psy = power_supply_register(&pdev->dev, &ac_desc, &cfg);
    if (IS_ERR(ac_psy))
        goto err_ac;

    return 0;

err_ac:
    power_supply_unregister(bat_psy);
err_bat:
    platform_device_unregister(pdev);
    return -ENODEV;
}

static void __exit pspi_battery_exit(void)
{
    power_supply_unregister(ac_psy);
    power_supply_unregister(bat_psy);
    platform_device_unregister(pdev);
}

module_init(pspi_battery_init);
module_exit(pspi_battery_exit);

MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("PSPi userspace-driven battery");
