import embed from "vega-embed";
import { navigate } from "svelte-routing"; // Import navigate for navigation

export function createBarChart(container, sortedSellers) {
  // Remove the existing chart if it exists
  const barChartContainer = document.getElementById(container);
  barChartContainer.innerHTML = "";

  // Sort sellers by count in descending order
  sortedSellers = sortedSellers.sort((a, b) => b.count - a.count);

  // Limit to the top 10 sellers
  sortedSellers = sortedSellers.slice(0, 10);

  // Define the Vega-Lite specification
  const spec = {
    $schema: "https://vega.github.io/schema/vega-lite/v5.json",
    description: "Bar Chart of Sellers",
    width: 350, // Chart width
    height: 250, // Chart height
    data: {
      values: sortedSellers,
    },
    mark: {
      type: "bar",
      tooltip: true,
    },
    encoding: {
      x: {
        field: "seller",
        type: "ordinal",
        sort: "-y", // Explicitly sort by the y-axis (count) in descending order
        axis: {
          title: "Sellers",
          titleFontSize: 16,
          labelFontSize: 12,
          labelAngle: -45, // Rotate labels for better readability
        },
      },
      y: {
        field: "count",
        type: "quantitative",
        axis: {
          title: "Count",
          titleFontSize: 16,
          labelFontSize: 12,
        },
      },
      color: {
        field: "count", // Use count to determine the color intensity
        type: "quantitative",
        scale: { scheme: "purples" }, // Use the "purples" color scheme
        legend: null, // Remove the color legend
      },
    },
    title: {
      text: "Sellers of Selected Product and Animal",
      fontSize: 20,
      fontWeight: "bold",
      anchor: "middle",
    },
  };

  // Embed the Vega-Lite chart
  embed(barChartContainer, spec, { actions: false }).then((result) => {
    // Add click event listener
    result.view.addEventListener("click", (event, item) => {
      if (item && item.datum) {
        const seller = item.datum.seller; // Get the seller from the clicked bar
        navigate(`/search/seller?q=${encodeURIComponent(seller)}`);
      }
    });
  });
}
