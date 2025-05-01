import embed from "vega-embed";

export function createChart(chartData, productsCount, speciesCount, HandleClick) {
  // Remove the existing chart if it exists
  const heatmapContainer = document.getElementById("heatmap");
  heatmapContainer.innerHTML = "";

  // Step 1: Aggregate the data into disproportionateProductData
  let aggregatedData = chartData.reduce((acc, { products, animalName }) => {
    acc[products] = acc[products] || {};
    if (animalName && products) {
      acc[products][animalName] = (acc[products][animalName] || 0) + 1;
    }
    return acc;
  }, {});

  let disproportionateProductData = Object.entries(aggregatedData).map(
    ([productType, speciesData]) => ({
      productType,
      species: Object.entries(speciesData).map(([species, count]) => ({
        species,
        count,
      })),
    })
  );

  // Step 2: Calculate the total ad count for each product type and sort by total ad count
  disproportionateProductData = disproportionateProductData
    .map((d) => ({
      ...d,
      totalAdCount: d.species.reduce(
        (total, species) => total + species.count,
        0
      ),
    }))
    .sort((a, b) => b.totalAdCount - a.totalAdCount) // Sort by total ad count in descending order
    .slice(0, productsCount); // Take the top `productsCount` products

  // Step 3: Flatten the species across all product types and sort by ad count
  let allSpecies = disproportionateProductData.flatMap((d) =>
    d.species.map((s) => ({
      productType: d.productType,
      species: s.species,
      count: s.count,
    }))
  );

  // Step 4: Sort all species by their ad count in descending order
  allSpecies = allSpecies.sort((a, b) => b.count - a.count);

  // Step 5: Select the top `speciesCount` species from the sorted list
  const topSpecies = allSpecies.slice(0, speciesCount);

  // Step 6: For each product type, filter its species to only include the top `speciesCount` species
  disproportionateProductData = disproportionateProductData.map((d) => ({
    productType: d.productType,
    species: d.species.filter((s) =>
      topSpecies.some((ts) => ts.species === s.species)
    ),
  }));

  // Step 7: Flatten the final data to get the structure we want
  const flatData = disproportionateProductData.flatMap((d) =>
    d.species.map((s) => ({
      productType: d.productType,
      species: s.species,
      count: s.count,
    }))
  );

  // Step 8: Extract unique product types and species
  const productTypes = [...new Set(flatData.map((d) => d.productType))];
  const species = [...new Set(flatData.map((d) => d.species))];

  // Step 9: Create a complete dataset, filling in missing combinations with null counts
  const completeData = productTypes.flatMap((productType) =>
    species.map((specie) => {
      const match = flatData.find(
        (d) => d.productType === productType && d.species === specie
      );
      return {
        productType,
        species: specie,
        count: match ? match.count : null, // Null for missing data
      };
    })
  );

  // Define the Vega-Lite specification
  const spec = {
    $schema: "https://vega.github.io/schema/vega-lite/v5.json",
    description: "Heatmap of Product Types and Species",
    width: 600, // Adjusted width
    height: 400, // Adjusted height
    data: {
      values: completeData,
    },
    mark: {
      type: "rect",
      stroke: "white", // Add borders around the squares
      strokeWidth: 1, // Border thickness
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
        scale: { scheme: "purples" }, // Use the "purples" color scheme
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
