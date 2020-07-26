from ._image import Image


class File(Image):
    """A setting that provides image names loaded from files"""

    def __init__(
        self,
        text,
        value="Do not use",
        can_be_blank=False,
        blank_text="Leave blank",
        *args,
        **kwargs,
    ):
        kwargs = kwargs.copy()
        if "required_attributes" not in kwargs:
            kwargs["required_attributes"] = {}
        kwargs["required_attributes"]["file_image"] = True
        super(File, self).__init__(
            text, value, can_be_blank, blank_text, *args, **kwargs
        )
