#pragma once
#ifdef __cplusplus
#include <version>
#include <cstring>
#include <type_traits>
#if !defined(__cpp_lib_bit_cast)
#include <bit>
namespace std {
template <class To, class From>
constexpr To bit_cast(const From& from) noexcept { return __builtin_bit_cast(To, from); }
}
#endif
#endif
