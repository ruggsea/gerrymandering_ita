"""
Data loading utilities for Italian electoral and geographic data.
"""
import pandas as pd
import geopandas as gpd
import logging
from pathlib import Path


def load_emilia_romagna_data(data_dir: str = ".") -> gpd.GeoDataFrame:
    """
    Load Emilia-Romagna voting and geographic data.

    Args:
        data_dir: Directory containing data files

    Returns:
        GeoDataFrame with commune geometries and voting data
    """
    data_dir = Path(data_dir)

    logging.info("Loading electoral data")
    voting_df = pd.read_csv(data_dir / "politiche_2022_liste_camera_comuni.csv")

    logging.info("Loading geographic data")
    geo_df = gpd.read_file(data_dir / "gerrymandering_base.geojson")

    # Filter for Emilia-Romagna
    emilia_voting = voting_df[
        voting_df['CIRCOSCRIZIONE'].str.contains('EMILIA', na=False)
    ].copy()

    logging.info(f"Found {len(emilia_voting)} communes in Emilia-Romagna")

    # Merge voting data with geometries
    emilia_voting['name'] = emilia_voting['name'].str.strip()
    geo_df['name'] = geo_df['name'].str.strip()

    gdf = geo_df.merge(
        emilia_voting,
        on='name',
        how='inner',
        suffixes=('_geo', '_vote')
    )

    # Use geometry from geo_df
    if 'geometry_geo' in gdf.columns:
        gdf = gdf.drop(columns=['geometry_vote'])
        gdf = gdf.rename(columns={'geometry_geo': 'geometry'})

    logging.info(f"Merged data: {len(gdf)} communes with complete data")

    # Add population estimate (voters as proxy)
    if 'population' not in gdf.columns:
        # Sum votes across all parties as population proxy
        party_cols = [col for col in gdf.columns if col.isupper() and gdf[col].dtype in ['float64', 'int64']]
        gdf['population'] = gdf[party_cols].sum(axis=1)

    return gdf


def get_major_parties() -> dict:
    """
    Return dictionary of major Italian parties and their abbreviations.

    Returns:
        Dictionary mapping party names to descriptions
    """
    return {
        "FRATELLI D'ITALIA CON GIORGIA MELONI": "Right",
        "LEGA PER SALVINI PREMIER": "Right",
        "FORZA ITALIA": "Right",
        "PARTITO DEMOCRATICO - ITALIA DEMOCRATICA E PROGRESSISTA": "Left",
        "ALLEANZA VERDI E SINISTRA": "Left",
        "MOVIMENTO 5 STELLE": "Populist",
        "AZIONE - ITALIA VIVA - CALENDA": "Center"
    }


def create_coalition_columns(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Add coalition voting columns (left, right, center).

    Args:
        gdf: GeoDataFrame with party voting data

    Returns:
        GeoDataFrame with added coalition columns
    """
    parties = get_major_parties()

    # Right coalition
    right_parties = [k for k, v in parties.items() if v == "Right"]
    right_cols = [col for col in gdf.columns if any(p in col for p in right_parties)]
    if right_cols:
        gdf['coalition_right'] = gdf[right_cols].sum(axis=1)

    # Left coalition
    left_parties = [k for k, v in parties.items() if v == "Left"]
    left_cols = [col for col in gdf.columns if any(p in col for p in left_parties)]
    if left_cols:
        gdf['coalition_left'] = gdf[left_cols].sum(axis=1)

    # Center
    center_parties = [k for k, v in parties.items() if v == "Center"]
    center_cols = [col for col in gdf.columns if any(p in col for p in center_parties)]
    if center_cols:
        gdf['coalition_center'] = gdf[center_cols].sum(axis=1)

    logging.info("Added coalition columns")
    return gdf


def load_and_prepare_data(
    region: str = "emilia",
    data_dir: str = ".",
    add_coalitions: bool = True
) -> gpd.GeoDataFrame:
    """
    Load and prepare data for analysis.

    Args:
        region: Region to analyze (currently only 'emilia' supported)
        data_dir: Directory containing data files
        add_coalitions: Whether to add coalition columns

    Returns:
        Prepared GeoDataFrame
    """
    if region.lower() == "emilia":
        gdf = load_emilia_romagna_data(data_dir)
    else:
        raise ValueError(f"Region {region} not yet supported")

    if add_coalitions:
        gdf = create_coalition_columns(gdf)

    return gdf
