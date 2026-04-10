import strawberry

from openoma_server.graphql.types.common import JSON


@strawberry.input
class PortDescriptorInput:
    name: str
    description: str = ""
    required: bool = True
    schema_def: JSON | None = strawberry.field(default=None, name="schema")
    metadata: JSON | None = None


@strawberry.input
class ExpectedOutcomeInput:
    name: str
    description: str = ""
    schema_def: JSON | None = strawberry.field(default=None, name="schema")
    metadata: JSON | None = None


@strawberry.input
class CreateWorkBlockInput:
    name: str
    description: str = ""
    inputs: list[PortDescriptorInput] | None = None
    outputs: list[PortDescriptorInput] | None = None
    execution_hints: list[str] | None = None
    expected_outcome: ExpectedOutcomeInput | None = None
    metadata: JSON | None = None


@strawberry.input
class UpdateWorkBlockInput:
    name: str | None = None
    description: str | None = None
    inputs: list[PortDescriptorInput] | None = None
    outputs: list[PortDescriptorInput] | None = None
    execution_hints: list[str] | None = None
    expected_outcome: ExpectedOutcomeInput | None = strawberry.UNSET
    metadata: JSON | None = None
