# types.py - UI コンポーネント用型エイリアス

"""UI コンポーネントで利用する型エイリアスを定義します。"""

from typing import Type, Union

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pubsubtk.ui.base.container_base import ContainerComponentTk, ContainerComponentTtk
    from pubsubtk.ui.base.presentational_base import PresentationalComponentTk, PresentationalComponentTtk
    from pubsubtk.ui.base.template_base import TemplateComponentTk, TemplateComponentTtk

# Container component types
ContainerComponentType = Union[Type["ContainerComponentTk"], Type["ContainerComponentTtk"]]

# Presentational component types  
PresentationalComponentType = Union[Type["PresentationalComponentTk"], Type["PresentationalComponentTtk"]]

# Template component types
TemplateComponentType = Union[Type["TemplateComponentTk"], Type["TemplateComponentTtk"]]

# Combined component type for general use
ComponentType = Union[ContainerComponentType, PresentationalComponentType]
