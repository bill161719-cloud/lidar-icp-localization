"""Apply the documented VTK dependency-discovery fix to PCL 1.15.1 only."""

import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    path = args.source / "cmake" / "pcl_find_vtk.cmake"
    original = path.read_text(encoding="utf-8")
    text = original
    replacements = [
        (
            "find_package(VTK)\n",
            "# Project fix: query only the desktop PCL modules, not all optional VTK backends.\n"
            "find_package(VTK COMPONENTS\n"
            "  ChartsCore CommonColor CommonComputationalGeometry CommonCore CommonDataModel\n"
            "  CommonExecutionModel CommonMath CommonMisc CommonTransforms FiltersCore\n"
            "  FiltersExtraction FiltersGeneral FiltersGeometry FiltersModeling FiltersSources\n"
            "  ImagingCore ImagingSources InteractionImage InteractionStyle InteractionWidgets\n"
            "  IOCore IOGeometry IOImage IOLegacy IOPLY RenderingAnnotation RenderingCore\n"
            "  RenderingContext2D RenderingLOD RenderingFreeType ViewsCore ViewsContext2D\n"
            "  RenderingOpenGL2 RenderingContextOpenGL2)\n",
        ),
        (
            'if("vtkGUISupportQt" IN_LIST VTK_MODULES_ENABLED)',
            'if(NOT WITH_QT STREQUAL "NO" AND "vtkGUISupportQt" IN_LIST VTK_MODULES_ENABLED)',
        ),
        (
            'elseif("GUISupportQt" IN_LIST VTK_AVAILABLE_COMPONENTS AND "RenderingQt" IN_LIST VTK_AVAILABLE_COMPONENTS)',
            'elseif(NOT WITH_QT STREQUAL "NO" AND "GUISupportQt" IN_LIST VTK_AVAILABLE_COMPONENTS AND "RenderingQt" IN_LIST VTK_AVAILABLE_COMPONENTS)',
        ),
    ]
    for old, new in replacements:
        if new in text:
            continue
        if text.count(old) != 1:
            raise RuntimeError(f"Unexpected PCL source: expected exactly one {old!r}")
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8", newline="\n")
    print("PCL 1.15.1 VTK discovery fix applied (idempotent).")


if __name__ == "__main__":
    main()
