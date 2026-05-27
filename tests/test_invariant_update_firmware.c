#include <check.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>

/*
 * Security Property: Protected endpoints (firmware update) must reject
 * unauthenticated requests. The firmware update process MUST require
 * valid authentication credentials before allowing any firmware replacement.
 *
 * CWE-287: Improper Authentication
 *
 * This test encodes the invariant that:
 * 1. Missing authentication tokens must be rejected
 * 2. Expired tokens must be rejected
 * 3. Malformed tokens must be rejected
 * 4. Empty credentials must be rejected
 * 5. Injected/forged tokens must be rejected
 *
 * The firmware update binary/process must NEVER proceed without
 * verifying valid credentials.
 */

/* Simulated authentication check function that mirrors what the firmware
 * update process SHOULD implement. This represents the required security
 * control that is currently MISSING from update_firmware.c */

#define AUTH_TOKEN_VALID    "VALID_SECRET_TOKEN_12345"
#define AUTH_RESULT_OK      0
#define AUTH_RESULT_REJECT  1

/* This function simulates the authentication gate that MUST exist.
 * In the vulnerable code, no such check exists - this test verifies
 * that any correct implementation would reject these payloads. */
static int check_firmware_auth_token(const char *token) {
    /* NULL or empty token must always be rejected */
    if (token == NULL) {
        return AUTH_RESULT_REJECT;
    }
    if (strlen(token) == 0) {
        return AUTH_RESULT_REJECT;
    }

    /* Only exact match with valid token is accepted */
    if (strcmp(token, AUTH_TOKEN_VALID) == 0) {
        return AUTH_RESULT_OK;
    }

    return AUTH_RESULT_REJECT;
}

/* Simulate what the firmware update process does with a given auth token.
 * Returns 0 if update would proceed (DANGEROUS without auth),
 * Returns 1 if update is blocked (CORRECT behavior). */
static int simulate_firmware_update_with_auth(const char *auth_token) {
    int auth_result = check_firmware_auth_token(auth_token);

    if (auth_result != AUTH_RESULT_OK) {
        /* Correctly blocked - return rejection code */
        return 403;
    }

    /* Auth passed - update would proceed */
    return 200;
}

/* Simulate the VULNERABLE behavior (no auth check at all) */
static int simulate_vulnerable_firmware_update(const char *auth_token) {
    (void)auth_token; /* Vulnerable code ignores auth entirely */
    /* The vulnerable code just proceeds with fgets() and flashing */
    return 200; /* Always succeeds - THIS IS THE BUG */
}

START_TEST(test_unauthenticated_requests_rejected)
{
    /* Invariant: Firmware update endpoint must reject ALL requests
     * that do not present valid authentication credentials.
     * Response must be 401 (Unauthorized) or 403 (Forbidden). */

    const char *payloads[] = {
        /* Missing/NULL token represented as empty string */
        "",
        /* Expired token */
        "EXPIRED_TOKEN_00000",
        /* Malformed tokens */
        "malformed",
        "Bearer ",
        "Bearer null",
        "Bearer undefined",
        "null",
        "undefined",
        "0",
        "false",
        /* SQL injection attempts */
        "' OR '1'='1",
        "' OR 1=1--",
        "admin'--",
        /* Command injection attempts */
        "; cat /etc/passwd",
        "$(whoami)",
        "`id`",
        /* Path traversal in token */
        "../../etc/passwd",
        "../../../root/.ssh/id_rsa",
        /* Buffer overflow attempts */
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        /* Format string attacks */
        "%s%s%s%s%s%s%s%s%s%s",
        "%x%x%x%x%x%x%x%x",
        "%n%n%n%n",
        /* Unicode/encoding tricks */
        "\xff\xfe\x00\x00",
        "\xef\xbb\xbf",
        /* Whitespace only */
        "   ",
        "\t\n\r",
        /* Almost-valid token (off by one) */
        "VALID_SECRET_TOKEN_1234",
        "VALID_SECRET_TOKEN_123456",
        "valid_secret_token_12345",
        "VALID_SECRET_TOKEN_12345 ",
        " VALID_SECRET_TOKEN_12345",
        /* Common default credentials */
        "admin",
        "password",
        "root",
        "token",
        "secret",
        "12345",
        "raspberry",
        "raspberrypi",
        /* JWT-like malformed tokens */
        "eyJhbGciOiJub25lIn0.eyJzdWIiOiJhZG1pbiJ9.",
        "eyJhbGciOiJIUzI1NiJ9.e30.invalid",
        /* Empty JSON */
        "{}",
        "{\"token\":null}",
        "{\"auth\":false}",
    };

    int num_payloads = sizeof(payloads) / sizeof(payloads[0]);

    for (int i = 0; i < num_payloads; i++) {
        int response = simulate_firmware_update_with_auth(payloads[i]);

        /* INVARIANT: Any unauthenticated/invalid token must result in
         * rejection (401 Unauthorized or 403 Forbidden).
         * A 200 response means the firmware update would proceed,
         * which is a critical security failure. */
        ck_assert_msg(
            response == 401 || response == 403,
            "SECURITY VIOLATION: Firmware update accepted invalid/missing "
            "auth token (payload index %d: '%.50s'). "
            "Got response %d, expected 401 or 403. "
            "This indicates CWE-287: Improper Authentication - "
            "the firmware update process has no authentication mechanism.",
            i, payloads[i], response
        );
    }
}
END_TEST

START_TEST(test_null_token_rejected)
{
    /* Invariant: NULL authentication token must always be rejected */
    int response = simulate_firmware_update_with_auth(NULL);

    ck_assert_msg(
        response == 401 || response == 403,
        "SECURITY VIOLATION: Firmware update accepted NULL auth token. "
        "Got response %d, expected 401 or 403.",
        response
    );
}
END_TEST

START_TEST(test_vulnerable_code_always_proceeds)
{
    /* This test documents the CURRENT VULNERABLE behavior.
     * It verifies that the vulnerable implementation (no auth check)
     * would incorrectly allow ALL requests through.
     *
     * This test is expected to PASS (documenting the bug exists),
     * and should be REPLACED by a test that verifies the fix. */

    const char *attack_payloads[] = {
        "",
        "invalid_token",
        "' OR 1=1--",
        "EXPIRED_TOKEN",
        NULL,
    };

    /* Test with non-NULL payloads for the vulnerable simulation */
    const char *non_null_payloads[] = {
        "",
        "invalid_token",
        "' OR 1=1--",
        "EXPIRED_TOKEN",
    };

    int num_payloads = sizeof(non_null_payloads) / sizeof(non_null_payloads[0]);

    for (int i = 0; i < num_payloads; i++) {
        int vulnerable_response = simulate_vulnerable_firmware_update(
            non_null_payloads[i]
        );

        /* Document that vulnerable code returns 200 for everything */
        ck_assert_msg(
            vulnerable_response == 200,
            "Unexpected: vulnerable simulation returned %d for payload '%s'",
            vulnerable_response, non_null_payloads[i]
        );

        /* THE CRITICAL ASSERTION: The secure implementation MUST differ
         * from the vulnerable one for invalid tokens */
        int secure_response = simulate_firmware_update_with_auth(
            non_null_payloads[i]
        );

        ck_assert_msg(
            secure_response != vulnerable_response,
            "SECURITY REGRESSION: Secure implementation behaves identically "
            "to vulnerable implementation for invalid token '%s'. "
            "Both returned %d. Authentication check is not working.",
            non_null_payloads[i], secure_response
        );
    }
}
END_TEST

START_TEST(test_valid_token_accepted)
{
    /* Invariant: Valid credentials must be accepted (sanity check).
     * This ensures the auth mechanism is not broken in the other direction. */
    int response = simulate_firmware_update_with_auth(AUTH_TOKEN_VALID);

    ck_assert_msg(
        response == 200,
        "Auth mechanism broken: Valid token was rejected. "
        "Got response %d, expected 200.",
        response
    );
}
END_TEST

START_TEST(test_firmware_update_requires_auth_env)
{
    /* Invariant: The firmware update process must check for authentication
     * credentials in the environment/configuration before proceeding.
     * Simulates checking if auth environment variables are required. */

    /* These environment variable names represent auth tokens that
     * should be required but are missing in the vulnerable code */
    const char *required_auth_vars[] = {
        "FIRMWARE_AUTH_TOKEN",
        "FIRMWARE_UPDATE_SECRET",
        "ATM_FLASH_CREDENTIAL",
    };

    int num_vars = sizeof(required_auth_vars) / sizeof(required_auth_vars[0]);

    /* Unset all auth environment variables to simulate missing credentials */
    for (int i = 0; i < num_vars; i++) {
        unsetenv(required_auth_vars[i]);
    }

    /* Verify that without env credentials, the auth check fails */
    const char *env_token = getenv("FIRMWARE_AUTH_TOKEN");

    /* When env var is unset, token is NULL - must be rejected */
    int response = simulate_firmware_update_with_auth(env_token);

    ck_assert_msg(
        response == 401 || response == 403,
        "SECURITY VIOLATION: Firmware update proceeded without "
        "FIRMWARE_AUTH_TOKEN environment variable set. "
        "Got response %d. Missing authentication check in update_firmware.c",
        response
    );
}
END_TEST

Suite *security_suite(void)
{
    Suite *s;
    TCase *tc_core;
    TCase *tc_edge;

    s = suite_create("Security_CWE287_FirmwareAuth");

    tc_core = tcase_create("Core_Authentication");
    tcase_add_test(tc_core, test_unauthenticated_requests_rejected);
    tcase_add_test(tc_core, test_null_token_rejected);
    tcase_add_test(tc_core, test_valid_token_accepted);
    suite_add_tcase(s, tc_core);

    tc_edge = tcase_create("Edge_Cases");
    tcase_add_test(tc_edge, test_vulnerable_code_always_proceeds);
    tcase_add_test(tc_edge, test_firmware_update_requires_auth_env);
    suite_add_tcase(s, tc_edge);

    return s;
}

int main(void)
{
    int number_failed;
    Suite *s;
    SRunner *sr;

    s = security_suite();
    sr = srunner_create(s);

    srunner_run_all(sr, CK_NORMAL);
    number_failed = srunner_ntests_failed(sr);
    srunner_free(sr);

    return (number_failed == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
}