# Root BUILD file - depends on both C++ and Java targets

# Main target that depends on C++ library
cc_binary(
    name = "main",
    srcs = ["main.cpp"],
    deps = ["//cpp:calculator"],
)

# Java library target (build it separately to ensure Java compilation happens)
# Reference the source file using proper Bazel label
java_library(
    name = "java_lib",
    srcs = ["//java:Greeter.java"],
    visibility = ["//visibility:public"],
)

