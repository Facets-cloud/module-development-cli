from jsonschema import Draft7Validator

# Main schema
yaml_schema = {
    "$schema": "https://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "intent": {"type": "string"},
        "flavor": {"type": "string"},
        "version": {"type": "string"},
        "description": {"type": "string"},
        "clouds": {
            "type": "array",
            "items": {"type": "string", "enum": ["aws", "azure", "gcp", "kubernetes"]},
        },
        "spec": Draft7Validator.META_SCHEMA,  # Use the nested object schema
        "outputs": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "pattern": r"^@[a-z0-9-_]+\/[a-z0-9-_]+",
                        },
                        "title": {"type": "string"},
                        "providers": {
                            "type": "object",
                            "patternProperties": {
                                ".*": {
                                    "type": "object",
                                    "properties": {
                                        "source": {"type": "string"},
                                        "version": {"type": "string"},
                                        "attributes": {
                                            "type": "object",
                                            "additionalProperties": True,
                                        },
                                    },
                                    "required": ["source", "attributes"],
                                }
                            },
                        },
                    },
                    "required": ["type"],
                }
            },
        },
        "inputs": {
            "type": "object",
            "patternProperties": {
                ".*": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "pattern": r"^@[a-z0-9-_]+\/[a-z0-9-_]+",
                        },
                        "providers": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["type"],
                }
            },
        },
        "sample": {
            "type": "object",
            "properties": {
                "kind": {"type": "string"},
                "flavor": {"type": "string"},
                "version": {"type": "string"},
                "spec": {"type": "object"},
            },
            "required": ["kind", "flavor", "version", "spec"],
        },
        "artifact_inputs": {
            "type": "object",
            "properties": {
                "primary": {
                    "type": "object",
                    "properties": {
                        "attribute_path": {
                            "type": "string",
                            "pattern": r"^spec\.[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)*$",
                        },
                        "artifact_type": {
                            "type": "string",
                            "enum": ["docker_image", "freestyle"],
                        },
                    },
                    "required": ["attribute_path", "artifact_type"],
                }
            },
            "required": ["primary"],
        },
        "metadata": Draft7Validator.META_SCHEMA,
        "iac": {
            "type": "object",
            "properties": {
                "validated_files": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "additionalProperties": True
        },
    },
    "required": ["intent", "flavor", "version", "description", "spec", "clouds"],
}

# Define a separate schema for the `spec` field
spec_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "x-ui-output-type": {"type": "string"},
        "x-ui-variable-ref": {"type": "boolean"},
        "x-ui-secret-ref": {"type": "boolean"},
        "x-ui-dynamic-enum": {
            "type": "string",
            "pattern": r"^spec\.([a-zA-Z0-9_-]+|\*)(\.[a-zA-Z0-9_-]+|\.\*)*$"
        },
        "x-ui-overrides-only": {"type": "boolean"},
        "x-ui-override-disable": {"type": "boolean"},
        "x-ui-toggle": {"type": "boolean"},
        "x-ui-yaml-editor": {"type": "boolean"},
        "x-ui-error-message": {"type": "string"},
        "x-ui-visible-if": {
            "type": "object",
            "properties": {
                "field": {"type": "string", "pattern": r"^spec\..+"},
                "values": {
                    "type": "array",
                    "minItems": 1,
                },
            },
            "required": ["field", "values"],
        },
    },
    "additionalProperties": {
        "patternProperties": {
            "^(?!x-ui).*": {"if": {"type": "object"}, "then": {"$ref": "#"}, "else": {}}
        }
    },
}

additional_properties_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {},
    "not": {"required": ["additionalProperties"]},
    "additionalProperties": {
        "patternProperties": {
            "^(?!x-ui).*": {"if": {"type": "object"}, "then": {"$ref": "#"}, "else": {}}
        }
    },
}
