# Fix Summary

The visual issues ("exploding points" and "flattened view") were due to how high-dimensional axes are projected and scaled by default. I have patched the `grandscatter` library source code to resolve this:

1.  **Fix "Exploding Points":**
    -   In high dimensions, basis vectors (axes) project to short lines, while data points often project further out.
    -   **Solution:** Updated `Scatterplot.ts` to automatically boost the default `axisLength` by `√(ndim/3)`. This ensures the visual axes are long enough to contain the data cloud.

2.  **Fix "Flattened View":**
    -   The default initialization (`circularBasis`) forced axes into a 2D circle, leaving little variance for the Z-axis (depth).
    -   **Solution:** Implemented `sphericalBasis` in `linalg.ts` (using a Fibonacci spiral on a sphere) and updated `Projection.ts` to use it by default for 3D projections. This guarantees a true volumetric initial view.

3.  **Applied Changes:**
    -   Rebuilt the widget (`pnpm build:widget`) to apply these changes to the Python environment.

You should now see a properly scaled 3D scatterplot in your Marimo app.
