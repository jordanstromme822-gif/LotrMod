# Runtime miss list from Jordan's PC (old exe, session ended 2026-11-07 01:50).
# 157.5M interpreted instructions over ~47 min of play (about 56k per second, small next to
# the GBA's 16.8M cycles per second), so these are cleanup for the next build, not a stutter cause.
# ARM (IWRAM / BIOS): 0x18 x8456, 0x120 x8456, 0x03000004 x1683, 0x03000094 x445, 0x03000AB4 x194,
#   0x03000B38 x11044, jump-table 0x03000C48/C78/C80/CB4 x11044, jump-table 0x03000DE0 x708,
#   E44 x194, E58 x19, EA0 x63326, 0x03001080 x6773
# Thumb (cart): 08016354 08017530 08017CFC 08017D58 08018504 08018664 0801CD24 08021D64 0802EC80
#   0802ED20(x3829, trigger update) 0802EDD4 080325D8 080326AC 080356E0 08035F84 080367F0 08036850
#   08045FD0 08046124(x1429, pot update) 08046214 08049108
