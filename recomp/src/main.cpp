#include "runtime.h"
#include "runtime_arm.h"
int main(int argc, char** argv) {
    gbarecomp::RunOptions opts;
    opts.builtin_game_name = "The Lord of the Rings: The Return of the King (USA, Europe)";
    opts.builtin_rom_sha1 = "ec3d126d37ea6e2ad7030d8a99cf87c6e46c03fd";
    return gbarecomp::run_game(argc, argv, opts);
}
