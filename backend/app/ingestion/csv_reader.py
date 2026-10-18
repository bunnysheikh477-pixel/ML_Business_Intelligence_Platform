
from io import BytesIO

import pandas as pd


def read_csv_file(content: bytes) -> pd.DataFrame:
    errors = []

    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            df = pd.read_csv(BytesIO(content), encoding=encoding)

            if df.empty or len(df.columns) == 0:
                raise ValueError("CSV contains no usable data.")

            return df

        except (UnicodeDecodeError, pd.errors.ParserError) as exc:
            errors.append(str(exc))

    raise ValueError(
        "Unable to read CSV. Check its encoding and formatting."
    )
