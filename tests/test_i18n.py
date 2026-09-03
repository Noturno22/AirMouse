import i18n


def test_license_block_strings_exist():
    for key in ("license.trial_remaining", "license.trial_ended",
                "license.trial_ended_sub", "license.activate_now",
                "license.revalidate_failed", "license.ledge_blocked",
                "license.has_key", "license.activate_key",
                "license.enter_key", "license.activate_failed",
                "license.needs_connection"):
        t = i18n.tr(key)
        assert t and t != key
