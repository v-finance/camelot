from enum import Enum

class DelegateType(str, Enum):

    ENUM = "EnumDelegate"
    COMBO_BOX = "ComboBoxDelegate"
    MANY2ONE = "Many2OneDelegate"
    FILE = "FileDelegate"
    DATE = "DateDelegate"
    DATETIME = "DateTimeDelegate"
    DB_IMAGE = "DbImageDelegate"
    FLOAT = "FloatDelegate"
    INTEGER = "IntegerDelegate"
    LABEL = "LabelDelegate"
    LOCAL_FILE = "LocalFileDelegate"
    MONTHS = "MonthsDelegate"
    ONE2MANY = "One2ManyDelegate"
    PLAIN_TEXT = "PlainTextDelegate"
    TEXT_EDIT = "TextEditDelegate"
    BOOL = "BoolDelegate"
    COLOR = "ColorDelegate"
    LANGUAGE = "LanguageDelegate"
    RICH_TEXT = "RichTextDelegate"
    STATUS = "StatusDelegate"
    NOTE = "NoteDelegate"

    def __str__(self) -> str:
        return self.value
