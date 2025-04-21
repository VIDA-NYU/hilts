import { Chart, registerables } from "chart.js";
import { MatrixController, MatrixElement } from "chartjs-chart-matrix";
import embed from "vega-embed";

Chart.register(...registerables, MatrixController, MatrixElement);

export function createChart(chartData, productsCount, speciesCount, HandleClick) {
  // Remove the existing chart if it exists
  const heatmapContainer = document.getElementById("heatmap");
  heatmapContainer.innerHTML = "";

  // Step 1: Aggregate the data
  const aggregatedData = chartData.reduce((acc, { products, animalName }) => {
    acc[products] = acc[products] || {};
    if (animalName && products) {
      acc[products][animalName] = (acc[products][animalName] || 0) + 1;
    }
    return acc;
  }, {});

  // Step 2: Transform aggregated data into a structured format
  let disproportionateProductData = Object.entries(aggregatedData).map(
    ([productType, speciesData]) => ({
      productType,
      species: Object.entries(speciesData).map(([species, count]) => ({
        species,
        count,
      })),
    })
  );

  // Step 3: Calculate total counts and sort
  disproportionateProductData = disproportionateProductData
    .map((d) => ({
      ...d,
      totalAdCount: d.species.reduce((total, s) => total + s.count, 0),
    }))
    .sort((a, b) => b.totalAdCount - a.totalAdCount) // Sort by total ad count
    .slice(0, productsCount); // Keep top `productsCount`

  // Step 4: Flatten species and sort by count
  let allSpecies = disproportionateProductData.flatMap((d) =>
    d.species.map((s) => ({
      productType: d.productType,
      species: s.species,
      count: s.count,
    }))
  );

  allSpecies = allSpecies.sort((a, b) => b.count - a.count);

  // Step 5: Select top `speciesCount` species
  const topSpecies = [...new Set(allSpecies.map((d) => d.species))].slice(
    0,
    speciesCount
  );

  // Step 6: Filter species for each product type
  disproportionateProductData = disproportionateProductData.map((d) => ({
    productType: d.productType,
    species: d.species.filter((s) => topSpecies.includes(s.species)),
  }));

  // Step 7: Create a complete dataset with missing combinations filled
  const productTypes = disproportionateProductData.map((d) => d.productType);
  const completeData = productTypes.flatMap((productType) =>
    topSpecies.map((species) => {
      const match = allSpecies.find(
        (d) => d.productType === productType && d.species === species
      );
      return {
        productType,
        species,
        count: match ? match.count : 0, // Fill missing combinations with 0
      };
    })
  );

  // Define the Vega-Lite specification
  const spec = {
    $schema: "https://vega.github.io/schema/vega-lite/v5.json",
    description: "Heatmap of Product Types and Species",
    width: 350,
    height: 250,
    data: {
      values: completeData,
    },
    mark: {
      type: "rect",
      stroke: "white",
      strokeWidth: 1,
    },
    encoding: {
      x: {
        field: "species",
        type: "ordinal",
        axis: {
          title: "Species",
          titleFontSize: 16,
          labelFontSize: 12,
        },
      },
      y: {
        field: "productType",
        type: "ordinal",
        axis: {
          title: "Product Types",
          titleFontSize: 16,
          labelFontSize: 12,
        },
      },
      color: {
        field: "count",
        type: "quantitative",
        scale: { scheme: "purples" },
        legend: {
          title: "Count",
          titleFontSize: 16,
          labelFontSize: 12,
        },
      },
      tooltip: [
        { field: "productType", type: "ordinal", title: "Product Type" },
        { field: "species", type: "ordinal", title: "Species" },
        { field: "count", type: "quantitative", title: "Count" },
      ],
    },
  };

  // Embed the Vega-Lite chart
  embed(heatmapContainer, spec, { actions: false }).then((result) => {
    // Add click event listener
    result.view.addEventListener("click", (event, item) => {
      if (item && item.datum) {
        const { productType, species } = item.datum;
        const matchingImages = chartData
          .filter(
            (item) => item.products === productType && item.animalName === species
          )
          .map((item) => item.image_path);
        const matchingData = chartData.filter(
          (item) => item.products === productType && item.animalName === species
        );
        HandleClick(matchingImages, matchingData);
      }
    });
  });
}
