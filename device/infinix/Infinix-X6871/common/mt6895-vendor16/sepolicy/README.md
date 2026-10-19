# Enforcing recovery policy

This policy is shared by the audited X6850, X6853 and X6850B Android 16 trees.
It is compiled from source with the OrangeFox 14.1 policy. Native PLATFORM init,
the device module set, fstab, DTB and boot configuration remain independent of
the recovery policy. Android normal boot uses the policy from the installed ROM.

## How it works

- Patch 05 removes the seven TWRP permissive domains and excludes debug `su`
  permissiveness from recovery. Recovery init always selects enforcing mode.
- Root ADB uses the enforcing `recovery` domain.
- Service managers use their standard domains. Gatekeeper, KeyMint, boot control,
  health and keystore use the corresponding standard HAL/keystore domains.
- Trustonic's daemon uses `mtk_recovery_tee`. Its stock device nodes are labeled
  `tee_device`; required DAC permissions apply only to this recovery daemon.
- File contexts label the actual DRM card, temporary keystore and bootstrap
  directory. Genfs labels cover bootprof and MTK LEDs. Persistent vendor data is
  not relabeled into new recovery-specific types.
- Custom recovery needs userdata access for FBE, file management and backup/
  restore. Patch 05 adds recovery-only exceptions to the corresponding AOSP
  neverallow rules. Rules for other domains remain in place. Explicit permissions
  are compiled with neverallow checks enabled; there is no allow-all policy.
- Stock build/fingerprint properties can be used by OrangeFox's crypto setup
  in recovery RAM. The ROM's on-disk build.prop files are not replaced.
- Recovery receives no permission to change enforcing mode or reload policy.

## Native credential handoff

Patch 06 checks the AIDL Gatekeeper transaction, preserves its native KeyMint
HardwareAuthToken directly, validates legacy HIDL token size, and checks the
keystore authorization transaction before opening the synthetic-password key.
Unavailable services or rejected tokens fail with a specific error; logs contain
neither credentials nor token contents. A successful Gatekeeper verification
does not by itself establish that keystore accepted the token or CE storage opened.

Gatekeeper and KeyMint run as system:system, matching the audited vendor init
files. KeyMint uses the stock RKP v1 argument. Recovery-created mcRegistry state
uses an exact context with permissions for Gatekeeper and the Trustonic daemon.
No restorecon action is added to the Android persist partition.

Metadata decryption, DE initialization and credential-protected CE decryption
must be reported separately. Mounting /data or counting media directories is
insufficient evidence of CE unlock. Check the actual user-0 decrypt result.

## Native file-contexts packaging

The original `file_contexts_text` fake package used `cp -fn` and did not declare
its actual output. Incremental builds could therefore keep an old flat
`/file_contexts` alongside a new policy. Patch 05 makes this a real ETC module,
with the merged contexts as its input and recovery/root/file_contexts as its
installed output. Context changes must trigger copying and ramdisk rebuilding.

## Required checks

1. Analyze the policy extracted from the packed RECOVERY CPIO:
   `sepolicy-analyze sepolicy permissive` must print nothing.
2. Check that image/ZIP policies and contexts match the source-built outputs.
3. Keep `SELINUX_IGNORE_NEVERALLOWS` disabled; neverallow failures are build errors.
4. Verify native static PLATFORM init, target modules/firmware, DTB/header/
   bootconfig, AVB hash and the ZIP's complete image/native recovery CPIO.
5. On the correct physical model, check enforcing mode and the running kernel
   policy, ADB, crypto services, FBE, display/touch, fastbootd and normal Android
   boot to system_server. Compile-time checks do not replace these device tests.

All artifact hashes and completed device-test results belong in the per-device
validation report. X6850 device results do not establish physical validation
for X6853 or X6850B. These are unofficial builds intended for target-model testers.
