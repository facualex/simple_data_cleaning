import logging
from pathlib import Path

import pandas as pd
import sweetviz as sv

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent / "reports"


def profile(
    df: pd.DataFrame, output_path=REPORTS_DIR, out_filename="profile.html"
) -> None:
    """Generate a sweetviz HTML report for df and write it to output_path/out_filename."""
    output_path.mkdir(exist_ok=True)
    report_path = output_path / out_filename

    report = sv.analyze(df)
    report.show_html(str(report_path), open_browser=False)
