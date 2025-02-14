
import * as d3 from 'd3';
// import { createChart2 } from './imagesChart';


export function createChart(chartData, productsCount, speciesCount, HandleClick) {

    const margin = { top: 100, right: 150, bottom: 150, left: 100 };

    d3.select("div#heatmap").select('svg').remove();

    const svg = d3.select("div#heatmap")
        .append("svg")
        .attr("preserveAspectRatio", "xMinYMin meet")
        .attr("viewBox", "0 0 1100 900")
        .classed("svg-content-responsive", true);

    // Access the size of the SVG container
    const svgNode = svg.node(); // Get the actual DOM element of the svg
    const visWidth = svgNode.getBoundingClientRect().width;
    const visHeight = svgNode.getBoundingClientRect().height;

    let aggregatedData = chartData.reduce((acc, { products, animalName }) => {
        // Ensure product type has an entry in the accumulator
        acc[products] = acc[products] || {};
        if (animalName && products) {//  # REMOVE NULL
        acc[products][animalName] = (acc[products][animalName] || 0) + 1;
        }
        return acc;
    }, {})
    // Step 1: Aggregate the data into disproportionateProductData
    let disproportionateProductData = Object.entries(aggregatedData).map(([productType, speciesData]) => ({
    productType,
    species: Object.entries(speciesData)
        .map(([species, count]) => ({ species, count })) // Include all species
    }));

    // Step 2: Calculate the total ad count for each product type and sort by total ad count
    disproportionateProductData = disproportionateProductData
    .map(d => ({
        ...d,
        totalAdCount: d.species.reduce((total, species) => total + species.count, 0) // Calculate total ad count for this product type
    }))
    .sort((a, b) => b.totalAdCount - a.totalAdCount) // Sort by total ad count in descending order
    .slice(0, productsCount); // Take the top `productsCount` products

    // Step 3: Flatten the species across all product types and sort by ad count
    let allSpecies = disproportionateProductData.flatMap(d =>
    d.species.map(s => ({
        productType: d.productType,
        species: s.species,
        count: s.count
    }))
    );

    // Step 4: Sort all species by their ad count in descending order
    allSpecies = allSpecies.sort((a, b) => b.count - a.count);

    // Step 5: Select the top `speciesCount` species from the sorted list
    const topSpecies = allSpecies.slice(0, speciesCount);

    // Step 6: For each product type, filter its species to only include the top `speciesCount` species
    disproportionateProductData = disproportionateProductData.map(d => ({
    productType: d.productType,
    species: d.species.filter(s => topSpecies.some(ts => ts.species === s.species)) // Keep only top species
    }));

    // Step 7: Flatten the final data to get the structure we want
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

    // Fill with a rectangle for visualization.
        // .append("rect")
        // .classed("rect", true)
        // .attr("width", 600)
        // .attr("height", 400);

    // Create the SVG
    // const svg = d3.select("#heatmap")
    // .attr("width", visWidth + margin.left + margin.right)
    // .attr("height", visHeight + margin.top + margin.bottom);

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
    .style("font-size", "16px");

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
    })
    .on("click", (event, d) => {
        const productType = d.productType;
        const species = d.species;

        const matchingImages = chartData.filter(item => item.products === productType && item.animalName === species)
                                       .map(item => item.image_path);
        const matchingData = chartData.filter(item => item.products === productType && item.animalName === species);
                                    //    .map(item => item.image_path);
        HandleClick(matchingImages, matchingData);
    });

    // Add text labels to the cells with data
    completeData.forEach(d => {
    if (d.count !== null) {
        g.append("text")
        .attr("x", x(d.species) + x.bandwidth() / 2)
        .attr("y", y(d.productType) + y.bandwidth() / 2)
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "middle")
        .attr("font-size", "16px")
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
    .style("text-anchor", "end")
    .style("font-size", "16pt");

    g.append("g").call(yAxis)
    .selectAll('text')
    .style("font-size", "16pt");

    // Add x-axis label
    svg.append("text")
    .attr("x", margin.left + visWidth / 2)
    .attr("y", visHeight + margin.top + margin.bottom - 80)
    .attr("text-anchor", "middle")
    .style("font-size", "18pt")
    .text("Species");

    // Add y-axis label
    svg.append("text")
    .attr("x", -(margin.top + visHeight / 2)) // Rotate and center vertically
    .attr("y", 20) // Positioned to the left of y-axis
    .attr("transform", "rotate(-90)")
    .attr("text-anchor", "middle")
    .style("font-size", "18pt")
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
    .attr("font-size", "16px")
    .attr("font-weight", "bold")
    .text("Count");

    // Add title
    svg.append("text")
    .attr("x", (visWidth + margin.left + margin.right) / 2)
    .attr("y", margin.top / 2)
    .attr("text-anchor", "middle")
    .attr("font-size", "16px")
    .attr("font-weight", "bold")
    .text("Sold Products types and Associated Animal Species");

    };

    export function updateChartSize(chartData, productsCount, speciesCount, HandleClick, svgId) {
        console.log("resize")
        const svg = d3.select(`#${svgId}`);
        const visWidth = svg.node().clientWidth;
        const visHeight = svg.node().clientHeight;
        createChart(chartData, productsCount, speciesCount, HandleClick, svgId); // Re-create chart with new dimensions
      }
