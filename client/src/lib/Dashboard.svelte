<script>
    // core components
    import {getProducts} from "./Api";
    import LineChart from "./cards/LineChart.svelte";
    import BarChart from "./cards/BarChart.svelte";
    // import CardPageVisits from "cards/CardPageVisits.svelte";
    // import CardSocialTraffic from ".cards/CardSocialTraffic.svelte";
    // export let location;
    import * as d3 from "d3";
    import { onMount } from "svelte";
    import { projectName } from "./stores";


    let chartData = [];
    let aggregatedData;
    let projectId = "default";

    projectName.subscribe((name) => {
      projectId = name;
    });

    const margin = { top: 100, right: 150, bottom: 150, left: 100 };
    const visWidth = 800 - margin.left - margin.right;
    const visHeight = 600 - margin.top - margin.bottom;

    const updateChartData = (msg) => {
      if (msg && msg.products && msg.animalName) {
        msg.productType.forEach(value => chartData.productType.push(value));
        msg.species.forEach(value => chartData.species.push(value));
      }
    }

    aggregatedData = chartData.reduce((acc, { products, animalName }) => {
        // Ensure product type has an entry in the accumulator
        acc[products] = acc[products] || {};
        acc[products][animalName] = (acc[products][animalName] || 0) + 1;
        return acc;
      }, {})
    console.log(aggregatedData)

    let disproportionateProductData = Object.entries(aggregatedData).map(([productType, speciesData]) => ({
        productType,
        species: Object.entries(speciesData)
          .map(([species, count]) => ({ species, count })) // Include all species
      }));


    const flatData = disproportionateProductData.flatMap(d =>
      d.species.map(s => ({
        productType: d.productType,
        species: s.species,
        count: s.count
      }))
    );

    // Extract unique product types and species
    const productTypes = [...new Set(flatData.map(d => d.productType))];
    const species = [...new Set(flatData.map(d => d.species))];

    // Create a complete dataset, filling in missing combinations with null counts
    const completeData = productTypes.flatMap(productType =>
      species.map(specie => {
        const match = flatData.find(d => d.productType === productType && d.species === specie);
        return {
          productType,
          species: specie,
          count: match ? match.count : null // Null for missing data
        };
      })
    );

    const createChart = () => {
      const x = d3.scaleBand()
        .domain(species)
        .range([0, visWidth])
        .padding(0.1);

      const y = d3.scaleBand()
        .domain(productTypes)
        .range([0, visHeight])
        .padding(0.1);

      const color = d3.scaleSequential(d3.interpolateBlues)
        .domain([0, d3.max(flatData, d => d.count)]);

      // Create the SVG
      const svg = d3.select("#svg")
        .attr("width", visWidth + margin.left + margin.right)
        .attr("height", visHeight + margin.top + margin.bottom);

      const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

      // Draw the heatmap cells
      g.selectAll("rect")
        .data(completeData) // Bind complete data to rectangles
        .join("rect")
        .attr("x", d => x(d.species))
        .attr("y", d => y(d.productType))
        .attr("width", x.bandwidth())
        .attr("height", y.bandwidth())
        .attr("fill", d => (d.count !== null ? color(d.count) : "#d3d3d3")) // Gray for missing data
        .attr("stroke", "#ccc") // Optional: Add a border for better visibility
        .attr("stroke-width", 0.5);

      // Tooltip
      const tooltip = d3.select("body").append("div")
        .style("position", "absolute")
        .style("visibility", "hidden")
        .style("background", "#f4f4f4")
        .style("border", "1px solid #ccc")
        .style("padding", "8px")
        .style("border-radius", "4px")
        .style("font-size", "12px");

      // Add interactivity to heatmap cells
      g.selectAll("rect")
        .on("mouseover", (event, d) => {
          tooltip
            .html(
              d.count !== null
                ? `<strong>Product Type:</strong> ${d.productType}<br>
                  <strong>Species:</strong> ${d.species}<br>
                  <strong>Count:</strong> ${d.count}`
                : `<strong>Product Type:</strong> ${d.productType}<br>
                  <strong>Species:</strong> ${d.species}<br>
                  <strong>Count:</strong> No data available`
            )
            .style("visibility", "visible");
          d3.select(event.target)
            .attr("stroke", "black")
            .attr("stroke-width", 1.5);
        })
        .on("mousemove", (event) => {
          tooltip
            .style("top", `${event.pageY - 10}px`)
            .style("left", `${event.pageX + 10}px`);
        })
        .on("mouseout", (event) => {
          tooltip.style("visibility", "hidden");
          d3.select(event.target)
            .attr("stroke", "#ccc")
            .attr("stroke-width", 0.5);
        });

      // Add text labels to the cells with data
      completeData.forEach(d => {
        if (d.count !== null) {
          g.append("text")
            .attr("x", x(d.species) + x.bandwidth() / 2)
            .attr("y", y(d.productType) + y.bandwidth() / 2)
            .attr("text-anchor", "middle")
            .attr("dominant-baseline", "middle")
            .attr("font-size", "10px")
            .attr("fill", d.count > 300 ? "white" : "black") // Adjust text color based on contrast
            .text(d.count);
        }
      });

      // Add axes
      const xAxis = d3.axisBottom(x).tickSize(0);
      const yAxis = d3.axisLeft(y).tickSize(0);

      g.append("g")
        .attr("transform", `translate(0,${visHeight})`)
        .call(xAxis)
        .selectAll("text")
        .attr("transform", "rotate(-45)")
        .style("text-anchor", "end");

      g.append("g").call(yAxis);

      // Add x-axis label
      svg.append("text")
        .attr("x", margin.left + visWidth / 2)
        .attr("y", visHeight + margin.top + margin.bottom - 80)
        .attr("text-anchor", "middle")
        .style("font-size", "14px")
        .text("Species");

      // Add y-axis label
      svg.append("text")
        .attr("x", -(margin.top + visHeight / 2)) // Rotate and center vertically
        .attr("y", 20) // Positioned to the left of y-axis
        .attr("transform", "rotate(-90)")
        .attr("text-anchor", "middle")
        .style("font-size", "14px")
        .text("Product Types");

      // Add color legend
      const legendHeight = 200;
      const legendWidth = 20;
      const legendMargin = 50; // Space between the heatmap and the legend

      const legendScale = d3.scaleLinear()
        .domain(color.domain()) // Use the same domain as the color scale
        .range([legendHeight, 0]);

      const legendAxis = d3.axisRight(legendScale).ticks(5);

      const legend = svg.append("g")
        .attr("transform", `translate(${visWidth + margin.left + legendMargin},${margin.top})`);

      const gradient = svg.append("defs")
        .append("linearGradient")
        .attr("id", "legend-gradient")
        .attr("x1", "0%")
        .attr("x2", "0%")
        .attr("y1", "0%")
        .attr("y2", "100%");

      gradient.append("stop")
        .attr("offset", "0%")
        .attr("stop-color", color(color.domain()[1]));

      gradient.append("stop")
        .attr("offset", "100%")
        .attr("stop-color", color(color.domain()[0]));

      legend.append("rect")
        .attr("width", legendWidth)
        .attr("height", legendHeight)
        .style("fill", "url(#legend-gradient)");

      legend.append("g")
        .attr("transform", `translate(${legendWidth}, 0)`)
        .call(legendAxis);

      legend.append("text")
        .attr("x", 25)
        .attr("y", -10)
        .attr("text-anchor", "end")
        .attr("font-size", "12px")
        .attr("font-weight", "bold")
        .text("Count");

      // Add title
      svg.append("text")
        .attr("x", (visWidth + margin.left + margin.right) / 2)
        .attr("y", margin.top / 2)
        .attr("text-anchor", "middle")
        .attr("font-size", "16px")
        .attr("font-weight", "bold")
        .text("Disproportionately Sold Products and Associated Animal Species");
    };

    // Initialize socket communication and call updateChartData on receiving data
    onMount(() => {
      chartData = getData()
      createChart(); // Re-create the chart with updated data
    })

    function getData() {
      chartData = getProducts(projectId)
      return chartData
    };

  </script>

  <div>
    <div class="flex flex-wrap">
      <div class="w-full xl:w-8/12 mb-12 xl:mb-0 px-4">
        <svg id="svg"></svg>
      </div>
      <!-- <div class="w-full xl:w-4/12 px-4">
        <BarChart />
      </div> -->
  </div>
</div>

