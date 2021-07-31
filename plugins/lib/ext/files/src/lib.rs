use pyo3::prelude::*;

#[pyfunction]
fn add(i: i64, j: i64) -> i64 {
    i + j
}

#[pymodule]
fn files(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(add, m)?)?;

    Ok(())
}