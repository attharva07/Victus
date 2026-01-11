from pathlib import Path

from victus.tools.regression_template import generate_template


def test_regression_template_generator_writes_expected_skeleton(tmp_path):
    out_path = tmp_path / "test_regression_demo.py"
    generate_template("demo-signature", out_path)
    content = out_path.read_text()

    assert "Regression test for signature: demo-signature" in content
    assert "pytest.mark.skip" in content
    assert "TODO implement reproducer" in content
