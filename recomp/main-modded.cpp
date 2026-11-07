#include "runtime.h"
#include "runtime_arm.h"
int main(int argc, char** argv) {
    gbarecomp::RunOptions opts;
    opts.builtin_game_name = "The Lord of the Rings: The Return of the King (USA, Europe) Modded";
    opts.builtin_rom_sha1 = "db6ec2d3d785f8d6ef426ebe5502d8aeabf6ab2e";
    return gbarecomp::run_game(argc, argv, opts);
}
