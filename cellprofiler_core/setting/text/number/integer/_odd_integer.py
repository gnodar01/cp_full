from cellprofiler_core.setting import Integer, ValidationError


class OddInteger(Integer):
    def test_valid(self, pipeline):
        super(self.__class__, self).test_valid(pipeline)

        value = self.str_to_value(self.value_text)

        if value % 2 == 0:
            raise ValidationError("Must be odd, was even", self)
