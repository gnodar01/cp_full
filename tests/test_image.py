"""test_Image.py - test the CellProfiler.Image module
"""

import math
import unittest

import numpy

import nucleus.image


class TestImage(unittest.TestCase):
    def test_init(self):
        nucleus.image.Image()

    def test_init_image(self):
        x = nucleus.image.Image(numpy.zeros((10, 10)))

    def test_init_image_mask(self):
        x = nucleus.image.Image(
            image=numpy.zeros((10, 10)), mask=numpy.ones((10, 10), dtype=numpy.bool)
        )

    def test_set_image(self):
        x = nucleus.image.Image()
        x.Image = numpy.ones((10, 10))

    def test_set_mask(self):
        x = nucleus.image.Image()
        x.Mask = numpy.ones((10, 10))

    def test_image_casts(self):
        one_target = numpy.ones((10, 10), dtype=numpy.float64)
        zero_target = numpy.zeros((10, 10), dtype=numpy.float64)
        tests = [
            (numpy.float64, 0, 1.0),
            (numpy.float32, 0, 1.0),
            (numpy.uint32, 0, math.pow(2.0, 32.0) - 1),
            (numpy.uint16, 0, math.pow(2.0, 16.0) - 1),
            (numpy.uint8, 0, math.pow(2.0, 8.0) - 1),
            (numpy.int32, -math.pow(2.0, 31.0), math.pow(2.0, 31.0) - 1),
            (numpy.int16, -math.pow(2.0, 15.0), math.pow(2.0, 15.0) - 1),
            (numpy.int8, -math.pow(2.0, 7.0), math.pow(2.0, 7.0) - 1),
        ]
        for dtype, zval, oval in tests:
            x = nucleus.image.Image()
            x.set_image((one_target * zval).astype(dtype))
            self.assertTrue(
                (x.image == zero_target).all(),
                msg="Failed setting %s to min" % (repr(dtype)),
            )
            x.set_image((one_target * oval).astype(dtype))
            y = x.image == one_target
            self.assertTrue(
                (x.image == one_target).all(),
                msg="Failed setting %s to max" % (repr(dtype)),
            )

    def test_mask_of3D(self):
        """The mask of a 3-d image should be 2-d"""
        x = nucleus.image.Image()
        x.image = numpy.ones((10, 10, 3))
        self.assertTrue(x.mask.ndim == 2)

    def test_cropping(self):
        x = nucleus.image.Image()
        x.image = numpy.ones((7, 7))
        crop_mask = numpy.zeros((10, 10), bool)
        crop_mask[2:-1, 1:-2] = True
        x.crop_mask = crop_mask
        i, j = numpy.mgrid[0:10, 0:10]
        test = i + j * 10
        test_out = x.crop_image_similarly(test)
        self.assertTrue(numpy.all(test_out == test[2:-1, 1:-2]))

    def test_init_volume(self):
        data = numpy.ones((5, 10, 10))

        x = nucleus.image.Image(image=data, dimensions=3)

        self.assertTrue(numpy.all(x.pixel_data == data))

        self.assertEqual(x.dimensions, 3)

    def test_multichannel_grayscale_image(self):
        data = numpy.ones((10, 10))

        x = nucleus.image.Image(image=data)

        self.assertFalse(x.multichannel)

    def test_multichannel_rgb_image(self):
        data = numpy.ones((10, 10, 3))

        x = nucleus.image.Image(image=data)

        self.assertTrue(x.multichannel)

    def test_multichannel_grayscale_volume(self):
        data = numpy.ones((5, 10, 10))

        x = nucleus.image.Image(image=data, dimensions=3)

        self.assertFalse(x.multichannel)

    def test_spacing_image_default(self):
        data = numpy.ones((5, 5))

        x = nucleus.image.Image(image=data)

        self.assertEqual(x.spacing, (1.0, 1.0))

    def test_spacing_image(self):
        data = numpy.ones((5, 5))

        x = nucleus.image.Image(image=data, spacing=(0.33, 0.33))

        self.assertEqual(x.spacing, (1.0, 1.0))

    def test_spacing_parent_image(self):
        data = numpy.ones((5, 5))

        px = nucleus.image.Image(image=data, spacing=(0.33, 0.33))

        x = nucleus.image.Image(image=data, parent_image=px)

        self.assertEqual(x.spacing, (1.0, 1.0))

    def test_spacing_volume_default(self):
        data = numpy.ones((5, 10, 10))

        x = nucleus.image.Image(image=data, dimensions=3)

        self.assertEqual(x.spacing, (1.0, 1.0, 1.0))

    def test_spacing_volume(self):
        data = numpy.ones((5, 10, 10))

        x = nucleus.image.Image(image=data, dimensions=3, spacing=(0.77, 0.33, 0.33))

        self.assertEqual(x.spacing, (0.77 / 0.33, 1.0, 1.0))

    def test_spacing_volume_parent_image(self):
        data = numpy.ones((5, 10, 10))

        px = nucleus.image.Image(image=data, dimensions=3, spacing=(0.77, 0.33, 0.33))

        x = nucleus.image.Image(image=data, parent_image=px, spacing=(0.77, 0.33, 0.33))

        self.assertEqual(x.spacing, (0.77 / 0.33, 1.0, 1.0))


class TestImageSet(unittest.TestCase):
    def test_add(self):
        x = nucleus.image.ImageSet(0, {}, {})
        x.add("image", nucleus.image.Image(numpy.zeros((10, 20))))
        self.assertEqual(len(x.providers), 1)
        self.assertEqual(x.providers[0].name, "image")

    def test_get_image(self):
        x = nucleus.image.ImageSet(0, {}, {})
        x.add("image", nucleus.image.Image(numpy.zeros((10, 20))))
        image = x.get_image("image")
        self.assertEqual(tuple(image.pixel_data.shape), (10, 20))

    def test_must_be_binary(self):
        x = nucleus.image.ImageSet(0, {}, {})
        x.add("image", nucleus.image.Image(numpy.zeros((10, 20), bool)))
        image = x.get_image("image", must_be_binary=True)
        self.assertEqual(tuple(image.pixel_data.shape), (10, 20))

    def test_must_be_binary_throws(self):
        x = nucleus.image.ImageSet(0, {}, {})
        x.add("image", nucleus.image.Image(numpy.zeros((10, 20), float)))
        self.assertRaises(ValueError, x.get_image, "image", must_be_binary=True)

    def test_must_be_gray(self):
        x = nucleus.image.ImageSet(0, {}, {})
        x.add("image", nucleus.image.Image(numpy.zeros((10, 20), float)))
        image = x.get_image("image", must_be_grayscale=True)
        self.assertEqual(tuple(image.pixel_data.shape), (10, 20))

    def test_must_be_gray_throws(self):
        x = nucleus.image.ImageSet(0, {}, {})
        numpy.random.seed(22)
        x.add("image", nucleus.image.Image(numpy.random.uniform(size=(10, 20, 3))))
        self.assertRaises(ValueError, x.get_image, "image", must_be_grayscale=True)

    def test_must_be_gray_color(self):
        x = nucleus.image.ImageSet(0, {}, {})
        x.add("image", nucleus.image.Image(numpy.zeros((10, 20, 3), float)))
        image = x.get_image("image", must_be_grayscale=True)
        self.assertEqual(tuple(image.pixel_data.shape), (10, 20))

    def test_must_be_color(self):
        x = nucleus.image.ImageSet(0, {}, {})
        x.add("image", nucleus.image.Image(numpy.zeros((10, 20, 3), float)))
        image = x.get_image("image", must_be_color=True)
        self.assertEqual(tuple(image.pixel_data.shape), (10, 20, 3))

    def test_must_be_color_throws(self):
        x = nucleus.image.ImageSet(0, {}, {})
        numpy.random.seed(22)
        x.add("image", nucleus.image.Image(numpy.random.uniform(size=(10, 20))))
        self.assertRaises(ValueError, x.get_image, "image", must_be_color=True)

    def test_must_be_rgb(self):
        x = nucleus.image.ImageSet(0, {}, {})
        x.add("image", nucleus.image.Image(numpy.zeros((10, 20, 3), float)))
        image = x.get_image("image", must_be_rgb=True)
        self.assertEqual(tuple(image.pixel_data.shape), (10, 20, 3))

    def test_must_be_rgb_throws_gray(self):
        x = nucleus.image.ImageSet(0, {}, {})
        numpy.random.seed(22)
        x.add("image", nucleus.image.Image(numpy.random.uniform(size=(10, 20))))
        self.assertRaises(ValueError, x.get_image, "image", must_be_rgb=True)

    def test_must_be_rgb_throws_5_channel(self):
        x = nucleus.image.ImageSet(0, {}, {})
        numpy.random.seed(22)
        x.add("image", nucleus.image.Image(numpy.random.uniform(size=(10, 20, 5))))
        self.assertRaises(ValueError, x.get_image, "image", must_be_rgb=True)

    def test_must_be_rgb_alpha(self):
        x = nucleus.image.ImageSet(0, {}, {})
        x.add("image", nucleus.image.Image(numpy.zeros((10, 20, 4), float)))
        image = x.get_image("image", must_be_rgb=True)
        self.assertEqual(tuple(image.pixel_data.shape), (10, 20, 3))


class TestImageSetList(unittest.TestCase):
    def test_init(self):
        x = nucleus.image.ImageSetList()
        self.assertEqual(
            x.count(),
            0,
            "# of elements of an empty image set list is %d, not zero" % (x.count()),
        )

    def test_add_image_set_by_number(self):
        x = nucleus.image.ImageSetList()
        y = x.get_image_set(0)
        self.assertEqual(
            x.count(), 1, "# of elements was %d, should be 1" % (x.count())
        )
        self.assertEqual(y.number, 0, "The image set should be #0, was %d" % y.number)
        self.assertTrue("number" in y.keys, "The image set was missing a number key")
        self.assertEqual(
            y.keys["number"],
            0,
            "The number key should be zero, was %s" % (repr(y.keys["number"])),
        )

    def test_add_image_set_by_key(self):
        x = nucleus.image.ImageSetList()
        key = {"key": "value"}
        y = x.get_image_set(key)
        self.assertEqual(
            x.count(), 1, "# of elements was %d, should be 1" % (x.count())
        )
        self.assertEqual(y.number, 0, "The image set should be #0, was %d" % y.number)
        self.assertEqual(
            y, x.get_image_set(0), "The image set should be retrievable by index"
        )
        self.assertEqual(
            y, x.get_image_set(key), "The image set should be retrievable by key"
        )
        self.assertEqual(repr(key), repr(y.keys))

    def test_add_two_image_sets(self):
        x = nucleus.image.ImageSetList()
        y = x.get_image_set(0)
        z = x.get_image_set(1)
        self.assertEqual(
            x.count(), 2, "# of elements was %d, should be 2" % (x.count())
        )
        self.assertEqual(y.number, 0, "The image set should be #0, was %d" % y.number)
        self.assertEqual(z.number, 1, "The image set should be #1, was %d" % y.number)
        self.assertEqual(
            y, x.get_image_set(0), "The first image set was not retrieved by index"
        )
        self.assertEqual(
            z, x.get_image_set(1), "The second image set was not retrieved by index"
        )

    def test_add_image_provider(self):
        x = nucleus.image.ImageSetList()
        y = x.get_image_set(0)
        img = nucleus.image.Image(numpy.ones((10, 10)))

        def fn(image_set, image_provider):
            self.assertEqual(
                y, image_set, "Callback was not called with the correct image provider"
            )
            return img

        z = nucleus.image.CallbackImageProvider("TestImageProvider", fn)
        y.providers.append(z)
        self.assertEqual(img, y.get_image("TestImageProvider"))

    def test_add_two_image_providers(self):
        x = nucleus.image.ImageSetList()
        y = x.get_image_set(0)
        img1 = nucleus.image.Image(numpy.ones((10, 10)))

        def fn1(image_set, image_provider):
            self.assertEqual(
                y, image_set, "Callback was not called with the correct image set"
            )
            return img1

        img2 = nucleus.image.Image(numpy.ones((5, 5)))

        def fn2(image_set, image_provider):
            self.assertEqual(
                y, image_set, "Callback was not called with the correct image set"
            )
            return img2

        y.providers.append(nucleus.image.CallbackImageProvider("IP1", fn1))
        y.providers.append(nucleus.image.CallbackImageProvider("IP2", fn2))
        self.assertEqual(img1, y.get_image("IP1"), "Failed to get correct first image")
        self.assertEqual(img2, y.get_image("IP2"), "Failed to get correct second image")

    def test_serialize_no_key(self):
        """Serialize an image list with no keys in the image sets"""
        x = nucleus.image.ImageSetList()
        for i in range(5):
            x.get_image_set(i)
        s = x.save_state()

        y = nucleus.image.ImageSetList()
        y.load_state(s)
        self.assertEqual(y.count(), 5)

    def test_serialize_key(self):
        x = nucleus.image.ImageSetList()
        values = (("A", "B"), ("C", "D"), ("E", "F"))
        for value1, value2 in values:
            d = {"K1": value1, "K2": value2}
            x.get_image_set(d)
        s = x.save_state()

        y = nucleus.image.ImageSetList()
        y.load_state(s)
        self.assertEqual(y.count(), len(values))
        for i in range(len(values)):
            image_set = y.get_image_set(i)
            self.assertTrue(isinstance(image_set, nucleus.image.ImageSet))
            value1, value2 = values[i]
            for key, value in (("K1", value1), ("K2", value2)):
                self.assertEqual(image_set.keys[key], value)

    def test_serialize_legacy_fields(self):
        x = nucleus.image.ImageSetList()
        for i in range(5):
            x.get_image_set(i)
        d = {"foo": "bar", "test": "suite"}
        x.legacy_fields["dictionary"] = d
        s = x.save_state()

        y = nucleus.image.ImageSetList()
        y.load_state(s)
        self.assertEqual(y.count(), 5)
        self.assertTrue("dictionary" in y.legacy_fields)
        for key in list(d.keys()):
            self.assertTrue(key in y.legacy_fields["dictionary"])
            self.assertEqual(y.legacy_fields["dictionary"][key], d[key])
