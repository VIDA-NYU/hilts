import * as d3 from 'd3';

export function createImageVisualization(imageUrls) {
    // Select the container for the images
    const container = d3.select("#image-grid");
    container.selectAll("*").remove();

    const svg = container.append("svg")
      .attr("width", 600)  // Set width for the image grid
      .attr("height", 400); // Set height for the image grid


    // Process the image URLs
    const imagePaths = imageUrls.map(url => {
      const path = url.split("/").pop();  // Get the last part of the URL (image name)
      return path;
    });

    // Add image elements to the SVG for each image URL
    const imageCards = svg.selectAll(".image-card")
      .data(imagePaths)
      .enter().append("g")
      .attr("class", "image-card")
      .attr("transform", (d, i) => {
        const x = (i % 5) * 120;  // 5 images per row (adjust width)
        const y = Math.floor(i / 5) * 120;  // Move to the next row after 5 images
        return `translate(${x}, ${y})`;
      });

    // Append image elements inside the cards
    imageCards.append("image")
      .attr("xlink:href", d => `/images/${d}`)  // Path to the image
      .attr("width", 100)
      .attr("height", 100)
      .attr("class", "image-card");
    }
