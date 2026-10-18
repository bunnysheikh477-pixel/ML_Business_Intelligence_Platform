
from io import BytesIO

import pandas as pd


def read_excel_file(content: bytes) -> pd.DataFrame:
    try:
        df = pd.read_excel(BytesIO(content), engine="openpyxl")

        if df.empty or len(df.columns) == 0:
            raise ValueError("Excel file contains no usable data.")

        return df

    except ValueError:
        raise

    except Exception as exc:
        raise ValueError(
            "Unable to read Excel file. Check that it is a valid XLSX file."
        ) from exc
