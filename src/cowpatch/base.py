import numpy as np
import plotnine as p9
from .svg_utils import gg_to_svg, _save_svg_wrapper
from .utils import to_inches, to_inches, inherits_plotnine

# TODO notes:
# 2/7 (Ben): patch object needs annotation functionality, * and & operators
#       to work with themes. And a lot of testing. I also think we need to
#       think about how to deal inputs that are UNwrapped plotnine ggplot
#       objects.

class patch:
    """
    general object to describe a plots or arangement of plots

    Arguments
    ---------
    *args : ggplots and patches
    grobs : list
        list of ggplot objects and patches. Either *args is empty or
        grobs is None.

    Notes
    -----
    All patch objects can be combined with other patch objects, either inside
    other `patch` calls or using mathematical grammar (described below).

    Additionally, patch objects's layouts can be described by adding a `layout`
    object, can have figure labels and titles added using an addition of a
    `annotation` object, and can have plots inset into it's grid with a
    `inset` object addition.

    **Mathematical Grammar**

    Mirroring ideas in `R`'s `patchwork` package, the following methods can
    be used to combine patch objects

    - `__add__` (`+`) of patches will (in the default) arange a sequence of
        patches in a matrix grid (byrow)
    - `__or__` (`|`) of patches will (in the default) arange a sequence of
        patches in a single row
    - `__div__` (`/`) of patches will (in the default) arange a sequence of
        patches in a single column

    These can also be combined to make complex layout structures. In addition,
    these structures can define depths structures. The top layout can be
    updated with an addition of a `layout`.

    Beyond combinations with other patches, the use of

    - `__mul__` (`*`) with a plotnine theme object will apply that theme to
        every plotnine object on the top layer (and `text` object - see
        document)
    - `__mul__` (`*`) with a plotnine theme object will apply that theme to
        every plotnine object at any depth (and `text` object - see document)

    """
    def __init__(self, *args, grobs=None):
        # todo put *args into a list
        args_grobs = [x for x in args]
        if len(args_grobs) > 0
            if grobs is not None:
                raise ValueError("cannot input a grobs list"+\
                                 " as well as individual plots")
            else:
                self.grobs = args_grobs
        else:
            self.grobs = grobs

        self.layout = "patch" # this is different than None...

    def _layout(self):
        """
        provide layout default else return layout
        """
        if self.layout == "patch":
            if len(self.grobs) < 4:
                return layout(nrow = len(self.grobs), ncol = 1)
            else:
                num_grobs = len(self.grobs)
                nrow = int(np.ceil(np.sqrt(num_grobs)))
                design = list(np.arange(num_grobs)) +\
                    [np.nan] * (nrow**2 - num_grobs)
                return layout(design = design)
        else:
            return self.layout

    def _check_layout(self):
        if self.layout().num_items != len(self.grobs):
            raise AttributeError("layout's number of patches does not "+\
                                 "matches number of patches in arangement")

    def __or__(self, other):
        # check proper usage -------
        if not inherits(other, patch):
            raise ValueError("only can connect specific general patch items"+\
                             " with \"|\".")

        # combine with other -------
        if self.layout is None:
            # only for wrappers!
            return patch(grobs=[self, other]) + layout(ncol=2,nrow=1)
        elif self.layout == layout(design == np.array([[0]])):
            # current self is [inner]
            return patch(grobs=self.grobs+[other]) + layout(ncol=2,nrow=1)
        elif self.layout.nrow == 1:
            # continuing a row
            return patch(grobs=self.grobs+[other]) + layout(nrow = 1, ncol = len(self.grobs)+1)
        else:
            return patch(grobs=[self.grobs]+[other]) + layout(ncol=2,nrow=1)

    def __div__(self, other):
        # check proper usage -------
        if not inherits(other, patch):
            raise ValueError("only can connect specific general patch items"+\
                             " with \"/\".")

        # combine with other -------
        if self.layout is None:
            # only for wrappers!
            return patch(grobs=[self, other]) + layout(ncol=1,nrow=2)
        elif self.layout == layout(design == np.array([[0]])):
            # current self is [inner]
            return patch(grobs=self.grobs+[other]) + layout(ncol=1,nrow=2)
        elif self.layout.nrow == 1:
            # continuing a row
            return patch(grobs=self.grobs+[other]) + layout(nrow = len(self.grobs)+1, ncol = 1)
        else:
            return patch(grobs=[self.grobs]+[other]) + layout(ncol=2,nrow=1)

    def __add__(self, other):
        # check proper usage -------
        if not inherits(other, patch) or \
            inherits(other, layout) or \
            inherits(other, annotation):
            if inherits(other,p9.theme):
                raise ValueError("cannot directly add a theme to a patch" +\
                                 " object unless a wrapper, try \"&\" or \"*\"")
            raise ValueError("only can connect specific general patch items"+\
                             " with \"/\".")


        if inherits(other, patch):
            # combine with other patch -------
            if self.layout is None:
                # only for wrappers!
                return patch(grobs=[self, other])
            elif self.layout == layout(design == np.array([[0]])):
                # current self is [inner]
                return patch(grobs=self.grobs+[other])
            elif self.layout.nrow == 1:
                # continuing a row
                return patch(grobs=self.grobs+[other])
            else:
                return patch(grobs=[self.grobs]+[other])
        elif inherits(other, layout):
            # combine with layout -------------
            self.layout = layout
        elif inherits(other, annotation):
            raise ValueError("currently not implimented addition with annotation")
            pass

    def __mul__(self, other):
        raise ValueError("currently not implimented *")
    def __and__(self, other):
        raise ValueError("currently not implimented &")


    def _svg(self, width_px, height_px):
        """
        Internal function to create an svg representation of the patch

        Arguments
        ---------
        width_px : float
            desired width of svg object in pixels
        height_px : float
            desired height of svg object in pixels

        Returns
        -------
        svg_object : svgutils.transforms object
        """
        self._check_layout()

        layout = self._layout()

        areas = layout._element_locations(width_px, height_px)
        #  TODO: should figure out how to arrange the notations here ...

        base_image = sg.SVGFigure()
        base_image.set_size((full_width_px, full_height_px)) # TODO: figure out if we're tracking pt vs px correct...
        # TODO: way to make decisions about the base image...
        base_image.append(
            sg.fromstring("<rect width=\"100%\" height=\"100%\" fill=\"#FFFFFF\"/>"))

        for p_idx in np.arange(len(self.grobs)):
            inner_area = areas[p_idx]

            inner_width_px = inner_area.width
            inner_height_px = inner_area.height

            inner_svg = self.grobs[p_idx]._svg(width_px = inner_width_px,
                                               height_px = inner_height_px)

            inner_root = inner_svg.getroot()

            inner_root.moveto(x=inner_area.x_left,
                              y=inner_area.y_top)
            base_image.append(inner_root)

        return base_image

    def save(self, filename, width, height, dpi=96, _format=None):
        """
        save patch to file

        Arguments
        ---------
        filename : str
            local string to save the file to (this can also be at a io.BytesIO)
        width : float
            width of output image in inches (this should actually be associated
            with the svg...)
        height : float
            height of svg in inches (this should actually be associated
            with the svg...)
        dpi : int or float
            dots per square inch, default is 96 (standard)
        _format : str
            string of format (error tells options). If provided this is the
            format used, if None, then we'll try to use the filename extension.

        Returns
        -------
        None
            saves to a file
        """
        # TODO: default width, height and dpi somewhere?
        svg_obj = self._svg(width_px = from_inches(width, "px", dpi=dpi),
                            height_px = from_inches(width, "px", dpi=dpi))

        _save_svg_wrapper(svg_obj,
                           filename=filename,
                           width=width,
                           height=height,
                           dpi=dpi,
                           _format=_format)
