from __future__ import absolute_import, print_function, division

from ufoLib.pointPen import AbstractPointPen

from fontPens.penTools import distance


class ThresholdPointPen(AbstractPointPen):
    """
    Rewrite of the ThresholdPen as a PointPen
    so that we can preserve named points and other arguments.
    This pen will add components from the original glyph, but
    but it won't filter those components.

    "move", "line", "curve" or "qcurve"
    """

    def __init__(self, otherPointPen, threshold=10):
        self.threshold = threshold
        self._lastPt = None
        self._offCurveBuffer = []
        self.otherPointPen = otherPointPen

    def beginPath(self, identifier=None, **kwargs):
        """Start a new sub path."""
        self.otherPointPen.beginPath(identifier) # how to add kwargs?
        self._lastPt = None

    def endPath(self):
        """End the current sub path."""
        self.otherPointPen.endPath()

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs):
        """Add a point to the current sub path."""
        if segmentType in (None, 'offcurve'):
            # it's an offcurve, let's buffer them until we get another oncurve
            # and we know what to do with them
            self._offCurveBuffer.append((pt, segmentType, smooth, name, identifier, kwargs))
            return

        elif segmentType == "move":
            # start of an open contour
            self.otherPointPen.addPoint(pt, segmentType, smooth, name, identifier) # how to add kwargs?
            self._lastPt = pt
            self._offCurveBuffer = []

        elif segmentType in ['line', 'curve', 'qcurve']:
            if self._lastPt is None:
                self.otherPointPen.addPoint(pt, segmentType, smooth, name, identifier) # how to add kwargs?
                self._lastPt = pt
            elif distance(pt, self._lastPt) >= self.threshold:
                # we're oncurve and far enough from the last oncurve
                if self._offCurveBuffer:
                    # empty any buffered offcurves
                    for buf_pt, buf_segmentType, buf_smooth, buf_name, buf_identifier, buf_kwargs in self._offCurveBuffer:
                        self.otherPointPen.addPoint(buf_pt, buf_segmentType, buf_smooth, buf_name, buf_identifier) # how to add kwargs?
                    self._offCurveBuffer = []
                # finally add the oncurve.
                self.otherPointPen.addPoint(pt, segmentType, smooth, name, identifier) # how to add kwargs?
                self._lastPt = pt
            else:
                # we're too short, so we're not going to make it.
                # we need to clear out the offcurve buffer.
                self._offCurveBuffer = []

    def addComponent(self, baseGlyphName, transformation, identifier=None, **kwargs):
        """Add a sub glyph. Note: this way components are not filtered."""
        self.otherPointPen.addComponent(baseGlyphName, transformation, identifier) # how to add kwargs?


def thresholdPointGlyph(aGlyph, threshold=10):
    """
    Convenience function that applies the **ThresholdPointPen** to a glyph in place.
    """
    from fontPens.recordingPointPen import RecordingPointPen
    recorder = RecordingPointPen()
    filterpen = ThresholdPointPen(recorder, threshold)
    aGlyph.drawPoints(filterpen)
    aGlyph.clear()
    recorder.replay(aGlyph.getPointPen())
    return aGlyph


# =========
# = tests =
# =========

def _makeTestGlyph():
    # make a simple glyph that we can test the pens with.
    from fontParts.nonelab import RGlyph
    testGlyph = RGlyph()
    testGlyph.name = "testGlyph"
    testGlyph.width = 1000
    pen = testGlyph.getPen()
    pen.moveTo((100, 100))
    pen.lineTo((900, 100))
    pen.lineTo((900, 109))
    pen.lineTo((900, 800))
    pen.curveTo((634, 800), (366, 800), (100, 800))
    pen.curveTo((100, 798), (100, 794), (100, 791))
    pen.closePath()
    pen.addComponent("a", (1, 0, 0, 1, 0, 0))
    return testGlyph


def _testThresholdPen():
    """
    >>> from fontPens.printPointPen import PrintPointPen
    >>> from random import seed
    >>> seed(100)
    >>> glyph = _makeTestGlyph()
    >>> pen = ThresholdPointPen(PrintPointPen())
    >>> glyph.drawPoints(pen)
    pen.beginPath()
    pen.addPoint((100, 100), segmentType='line')
    pen.addPoint((900, 100), segmentType='line')
    pen.addPoint((900, 800), segmentType='line')
    pen.addPoint((634, 800))
    pen.addPoint((366, 800))
    pen.addPoint((100, 800), segmentType='curve')
    pen.endPath()
    pen.addComponent('a', (1.0, 0.0, 0.0, 1.0, 0.0, 0.0))
    """


if __name__ == "__main__":
    import doctest
    doctest.testmod()
