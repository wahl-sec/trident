#include <pybind11/pybind11.h>
namespace py = pybind11;

int add(int i, int j) {
	return i + j;
}

PYBIND11_MODULE(_files, m) {
	py::module_ plugins = py::module_::import("plugins.lib.files");
	py::module_ files_ = plugins.def_submodule("files_", "");
	files_.def("add", &add, "Add two numbers.");
}
