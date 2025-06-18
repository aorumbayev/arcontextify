"""ARC-56 JSON specification parser."""

import json
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field


class ARC56Argument(BaseModel):
    """ARC-56 method argument."""

    name: str
    type: str
    description: str | None = None


class ARC56Method(BaseModel):
    """ARC-56 method definition."""

    name: str
    description: str | None = None
    args: list[ARC56Argument] = Field(default_factory=list)
    returns: dict[str, Any] | None = None
    readonly: bool = False
    actions: dict[str, list[str]] | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: dict[str, Any] | None = None


class ARC56Struct(BaseModel):
    """ARC-56 struct definition."""

    name: str
    elements: list[dict[str, Any]]


class ARC56Contract(BaseModel):
    """ARC-56 contract specification."""

    name: str
    description: str | None = None
    arcs: list[int] = Field(default_factory=lambda: [4, 56])  # Default ARCs
    structs: list[ARC56Struct] = Field(default_factory=list)
    methods: list[ARC56Method] = Field(default_factory=list)
    networks: dict[str, Any] | None = None
    source: dict[str, Any] | None = None
    state: dict[str, Any] | None = None
    bare_actions: dict[str, list[str]] | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    source_info: dict[str, Any] | None = None
    compiler_info: dict[str, Any] | None = None
    template_variables: dict[str, Any] | None = None
    scratch_variables: dict[str, Any] | None = None


def parse_arc56_file(file_path: str | Path) -> ARC56Contract:
    """Parse ARC-56 JSON file and return contract specification."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"ARC-56 file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    return _parse_contract_data(data)


def _parse_contract_data(data: dict[str, Any]) -> ARC56Contract:
    """Parse contract data from JSON."""
    # Parse structs - handle both dict and list formats
    structs: list[ARC56Struct] = []
    structs_data = data.get("structs", {})

    if isinstance(structs_data, dict):
        for name, elements in structs_data.items():
            if isinstance(elements, list):
                structs.append(ARC56Struct(name=name, elements=elements))
    elif isinstance(structs_data, list):
        for struct_data in structs_data:
            structs.append(
                ARC56Struct(
                    name=struct_data["name"], elements=struct_data.get("elements", [])
                )
            )

    # Parse methods
    methods = [
        ARC56Method(
            name=method["name"],
            description=method.get("description"),
            args=[
                ARC56Argument(
                    name=arg["name"],
                    type=arg["type"],
                    description=arg.get("description"),
                )
                for arg in method.get("args", [])
            ],
            returns=method.get("returns"),
            readonly=method.get("readonly", False),
            actions=method.get("actions"),
            events=method.get("events", []),
            recommendations=method.get("recommendations"),
        )
        for method in data.get("methods", [])
    ]

    return ARC56Contract(
        name=data.get("name", "UnnamedContract"),
        description=data.get("description"),
        arcs=data.get("arcs", [4, 56]),
        structs=structs,
        methods=methods,
        networks=data.get("networks"),
        source=data.get("source"),
        state=data.get("state"),
        bare_actions=data.get("bareActions"),
        events=data.get("events", []),
        source_info=data.get("sourceInfo"),
        compiler_info=data.get("compilerInfo"),
        template_variables=data.get("templateVariables"),
        scratch_variables=data.get("scratchVariables"),
    )


# Convenience class for backward compatibility
class ARC56Parser:
    """Legacy parser interface for ARC-56 JSON specifications."""

    def __init__(self, json_path: str) -> None:
        self.json_path = Path(json_path)
        self.contract: ARC56Contract | None = None

    def load(self) -> None:
        """Load and parse the ARC-56 JSON file."""
        self.contract = parse_arc56_file(self.json_path)

    def get_contract(self) -> ARC56Contract:
        """Get the parsed contract."""
        if self.contract is None:
            raise ValueError("Contract not loaded. Call load() first.")
        return self.contract
