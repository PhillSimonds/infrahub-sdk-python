from enum import Enum
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field
from typing_extensions import Self

from .ctl.exceptions import FileNotValidError
from .utils import find_files


class InfrahubFileApiVersion(str, Enum):
    V1 = "infrahub.app/v1"


class InfrahubFileKind(str, Enum):
    MENU = "Menu"
    OBJECT = "Object"


class InfrahubFileData(BaseModel):
    api_version: InfrahubFileApiVersion = Field(InfrahubFileApiVersion.V1, alias="apiVersion")
    kind: InfrahubFileKind
    spec: dict
    metadata: Optional[dict] = Field(default_factory=dict)


class LocalFile(BaseModel):
    identifier: Optional[str] = None
    location: Path
    content: Optional[dict] = None
    valid: bool = True
    error_message: Optional[str] = None


class YamlFile(LocalFile):
    def load_content(self) -> None:
        try:
            self.content = yaml.safe_load(self.location.read_text())
        except yaml.YAMLError:
            self.error_message = "Invalid YAML/JSON file"
            self.valid = False
            return

        if not self.content:
            self.error_message = "Empty YAML/JSON file"
            self.valid = False

    def validate_content(self) -> None:
        pass

    @classmethod
    def load_from_disk(cls, paths: list[Path]) -> list[Self]:
        yaml_files: list[Self] = []
        for file_path in paths:
            if file_path.is_file():
                yaml_file = cls(location=file_path)
                yaml_file.load_content()
                yaml_files.append(yaml_file)
            elif file_path.is_dir():
                files = find_files(extension=["yaml", "yml", "json"], directory=file_path)
                for item in files:
                    yaml_file = cls(location=item)
                    yaml_file.load_content()
                    yaml_files.append(yaml_file)
            else:
                raise FileNotValidError(name=str(file_path), message=f"{file_path} does not exist!")

        return yaml_files


class InfrahubFile(YamlFile):
    _data: Optional[InfrahubFileData] = None

    @property
    def data(self) -> InfrahubFileData:
        if not self._data:
            raise ValueError("_data hasn't been initialized yet")
        return self._data

    @property
    def version(self) -> InfrahubFileApiVersion:
        return self.data.api_version

    @property
    def kind(self) -> InfrahubFileKind:
        return self.data.kind

    def validate_content(self) -> None:
        if not self.content:
            raise ValueError("Content hasn't been loaded yet")
        self._data = InfrahubFileData(**self.content)


class SchemaFile(YamlFile):
    pass
