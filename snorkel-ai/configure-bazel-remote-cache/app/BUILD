# Root BUILD file - depends on both C++ and Java targets

# C++ library target
cc_library(
    name = "cpp_lib",
    srcs = ["//cpp:calculator"],
    hdrs = ["//cpp:calculator"],
    deps = [],
    visibility = ["//visibility:public"],
)

# Java library target
java_library(
    name = "java_lib",
    srcs = ["//java:greeter"],
    deps = [],
    visibility = ["//visibility:public"],
)

# Main target that depends on both
cc_binary(
    name = "main",
    srcs = ["main.cpp"],
    deps = [":cpp_lib"],
)

