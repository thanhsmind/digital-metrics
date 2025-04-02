import csv
import io
from typing import Any, Dict, List, Optional, Union

from fastapi.responses import StreamingResponse
from pydantic import BaseModel


async def generate_csv_response(
    data: List[Union[BaseModel, Dict[str, Any]]],
    filename: str,
    fields: Optional[List[str]] = None,
    include_bom: bool = True,
) -> StreamingResponse:
    """
    Generates a FastAPI StreamingResponse containing CSV data from a list of objects.

    Args:
        data: A list of Pydantic models or dictionaries to be converted to CSV rows.
              Assumes a homogeneous list (all items have similar structure).
              Handles nested dictionaries (like 'metrics') by flattening keys.
        filename: The desired filename for the downloaded CSV file.
        fields: An optional list of strings specifying the exact CSV columns and
                their order. If None, headers are dynamically generated from the
                first item in the data list.
        include_bom: Whether to include the UTF-8 Byte Order Mark (BOM) for better
                     Excel compatibility.

    Returns:
        A StreamingResponse object ready to be returned by a FastAPI endpoint.
    """
    output = io.StringIO()

    # Handle empty data case
    if not data:
        # Return an empty response or a response with just headers/message
        # For simplicity, return an empty CSV content
        if include_bom:
            output.write("\ufeff")
        # Optionally write headers even if empty:
        # if fields:
        #     writer = csv.DictWriter(output, fieldnames=fields, quoting=csv.QUOTE_MINIMAL)
        #     writer.writeheader()
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    # Flattening helper function
    def flatten_dict(
        d: Dict[str, Any], parent_key: str = "", sep: str = "."
    ) -> Dict[str, Any]:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    # Convert first item to dict and flatten to determine headers if needed
    first_item = data[0]
    first_item_dict = (
        first_item.dict() if isinstance(first_item, BaseModel) else first_item
    )
    flattened_first_item = flatten_dict(first_item_dict)

    fieldnames = fields if fields else list(flattened_first_item.keys())

    if include_bom:
        output.write("\ufeff")

    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
        quoting=csv.QUOTE_MINIMAL,
        extrasaction="ignore",
    )
    writer.writeheader()

    for item in data:
        item_dict = item.dict() if isinstance(item, BaseModel) else item
        flattened_item = flatten_dict(item_dict)
        writer.writerow(flattened_item)

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
