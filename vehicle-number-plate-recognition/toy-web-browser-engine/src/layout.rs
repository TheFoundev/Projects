//! A small block-layout engine implementing the CSS box model.

use crate::css::{compute_all_styles, ComputedStyle, StyleRule};
use crate::dom::{is_invisible_element, is_void_element, Node, NodeKind};

/// The four sides of a box.
#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct Edges {
    pub top: f64,
    pub right: f64,
    pub bottom: f64,
    pub left: f64,
}

impl Edges {
    /// Build edges from a CSS shorthand such as `1px 2px` or `1px 2px 3px 4px`.
    pub fn from_shorthand(value: &str) -> Edges {
        let mut parts = Vec::new();
        for part in value.split_whitespace() {
            if let Ok(number) = part.trim_end_matches("px").parse::<f64>() {
                parts.push(number);
            }
        }
        match parts.len() {
            0 => Edges::default(),
            1 => Edges {
                top: parts[0],
                right: parts[0],
                bottom: parts[0],
                left: parts[0],
            },
            2 => Edges {
                top: parts[0],
                right: parts[1],
                bottom: parts[0],
                left: parts[1],
            },
            3 => Edges {
                top: parts[0],
                right: parts[1],
                bottom: parts[2],
                left: parts[1],
            },
            _ => Edges {
                top: parts[0],
                right: parts[1],
                bottom: parts[2],
                left: parts[3],
            },
        }
    }
}

/// The computed geometry of a single box.
#[derive(Clone, Debug, PartialEq)]
pub struct BoxMetrics {
    pub margin: Edges,
    pub border: Edges,
    pub padding: Edges,
    /// Width of the content box in pixels.
    pub content_width: f64,
    /// Height of the content box in pixels.
    pub content_height: f64,
}

impl BoxMetrics {
    /// Total width of the box including margin, border and padding.
    pub fn total_width(&self) -> f64 {
        self.content_width
            + self.padding.left
            + self.padding.right
            + self.border.left
            + self.border.right
            + self.margin.left
            + self.margin.right
    }

    /// Total height of the box including margin, border and padding.
    pub fn total_height(&self) -> f64 {
        self.content_height
            + self.padding.top
            + self.padding.bottom
            + self.border.top
            + self.border.bottom
            + self.margin.top
            + self.margin.bottom
    }
}

/// A box placed on the canvas.
#[derive(Clone, Debug, PartialEq)]
pub struct LayoutBox {
    /// Tag name of the element.
    pub name: String,
    /// `id` attribute, when present.
    pub id: Option<String>,
    pub x: f64,
    pub y: f64,
    pub metrics: BoxMetrics,
}

impl LayoutBox {
    /// Left edge of the border box.
    pub fn border_x(&self) -> f64 {
        self.x + self.metrics.margin.left
    }

    /// Top edge of the border box.
    pub fn border_y(&self) -> f64 {
        self.y + self.metrics.margin.top
    }

    /// Outer width of the border box.
    pub fn width(&self) -> f64 {
        self.metrics.content_width
            + self.metrics.padding.left
            + self.metrics.padding.right
            + self.metrics.border.left
            + self.metrics.border.right
    }

    /// Outer height of the border box.
    pub fn height(&self) -> f64 {
        self.metrics.content_height
            + self.metrics.padding.top
            + self.metrics.padding.bottom
            + self.metrics.border.top
            + self.metrics.border.bottom
    }
}

/// Compute the box metrics of an element from its computed style.
///
/// `containing_width` is the width available to the element's content box.
pub fn compute_box(style: &ComputedStyle, containing_width: f64) -> BoxMetrics {
    let margin = Edges::from_shorthand(style.get_or("margin", "0"));
    let padding = Edges::from_shorthand(style.get_or("padding", "0"));
    let border = Edges::from_shorthand(style.get_or("border-width", "0"));
    let border_shorthand = style.get("border");
    let border = match border_shorthand {
        Some(value) if !value.contains("width") => Edges::from_shorthand(value),
        _ => border,
    };

    let content_width = match style.length("width", Some(containing_width)) {
        Some(width) => {
            if style.get_or("box-sizing", "content-box") == "border-box" {
                (width - padding.left - padding.right - border.left - border.right).max(0.0)
            } else {
                width.max(0.0)
            }
        }
        None => (containing_width
            - margin.left
            - margin.right
            - border.left
            - border.right
            - padding.left
            - padding.right)
            .max(0.0),
    };

    let content_height = style.length("height", None).unwrap_or(0.0);

    BoxMetrics {
        margin,
        border,
        padding,
        content_width,
        content_height: content_height.max(0.0),
    }
}

/// Lay out a document tree with a block layout algorithm.
///
/// Returns the boxes in document order.
pub fn layout(root: &Node, rules: &[StyleRule], viewport_width: f64) -> Vec<LayoutBox> {
    let styles = compute_all_styles(root, rules);
    let mut boxes = Vec::new();
    let mut style_index = 0;
    layout_children(
        root,
        &styles,
        &mut style_index,
        viewport_width,
        0.0,
        0.0,
        &mut boxes,
    );
    boxes
}

#[allow(clippy::too_many_arguments)]
fn layout_children(
    node: &Node,
    styles: &[ComputedStyle],
    style_index: &mut usize,
    containing_width: f64,
    x: f64,
    y: f64,
    boxes: &mut Vec<LayoutBox>,
) {
    let mut cursor = y;
    for child in &node.children {
        if child.kind != NodeKind::Element
            || is_void_element(&child.name)
            || is_invisible_element(&child.name)
        {
            continue;
        }
        let style = styles.get(*style_index).cloned().unwrap_or_default();
        *style_index += 1;
        let mut metrics = compute_box(&style, containing_width);
        let child_y = cursor + metrics.margin.top;
        let child_x = x + metrics.margin.left;

        let inner_width = metrics.content_width;
        let before = boxes.len();
        layout_children(
            child,
            styles,
            style_index,
            inner_width,
            child_x + metrics.border.left + metrics.padding.left,
            child_y + metrics.border.top + metrics.padding.top,
            boxes,
        );

        // Auto height grows with the content.
        if style.length("height", None).is_none() {
            let content_height = boxes[before..]
                .iter()
                .map(|child_box| child_box.metrics.total_height())
                .sum::<f64>();
            metrics.content_height = content_height;
        }

        cursor = child_y + metrics.total_height() - metrics.margin.top;
        boxes.push(LayoutBox {
            name: child.name.clone(),
            id: child.attribute("id").map(|value| value.to_string()),
            x: child_x,
            y: child_y,
            metrics,
        });
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::css::parse_stylesheet;
    use crate::dom::parse;

    #[test]
    fn content_box_adds_padding_border_and_margin() {
        let rules =
            parse_stylesheet("p { width: 100px; padding: 10px; border-width: 2px; margin: 5px }");
        let document = parse("<p>x</p>");
        let boxes = layout(&document, &rules, 800.0);
        let paragraph = boxes.iter().find(|entry| entry.name == "p").expect("p box");
        assert_eq!(paragraph.metrics.content_width, 100.0);
        assert_eq!(paragraph.width(), 100.0 + 20.0 + 4.0);
        assert_eq!(paragraph.metrics.total_width(), 100.0 + 20.0 + 4.0 + 10.0);
    }

    #[test]
    fn border_box_subtracts_padding_and_border_from_width() {
        let rules = parse_stylesheet(
            "p { box-sizing: border-box; width: 100px; padding: 10px; border-width: 2px }",
        );
        let document = parse("<p>x</p>");
        let boxes = layout(&document, &rules, 800.0);
        let paragraph = boxes.iter().find(|entry| entry.name == "p").unwrap();
        assert_eq!(paragraph.width(), 100.0);
    }

    #[test]
    fn auto_width_fills_the_containing_block() {
        let rules = parse_stylesheet("p { margin: 0 }");
        let document = parse("<p>x</p>");
        let boxes = layout(&document, &rules, 800.0);
        let paragraph = boxes.iter().find(|entry| entry.name == "p").unwrap();
        assert_eq!(paragraph.width(), 800.0);
    }

    #[test]
    fn blocks_stack_vertically() {
        let rules = parse_stylesheet("p { margin: 0; height: 20px }");
        let document = parse("<div><p>a</p><p>b</p></div>");
        let boxes = layout(&document, &rules, 800.0);
        let paragraphs: Vec<&LayoutBox> = boxes.iter().filter(|entry| entry.name == "p").collect();
        assert_eq!(paragraphs.len(), 2);
        assert_eq!(paragraphs[0].y, 0.0);
        assert_eq!(paragraphs[1].y, 20.0);
    }

    #[test]
    fn percentage_width_resolves_against_the_parent() {
        let rules = parse_stylesheet("div { width: 400px } p { width: 50% }");
        let document = parse("<div><p>x</p></div>");
        let boxes = layout(&document, &rules, 800.0);
        let paragraph = boxes.iter().find(|entry| entry.name == "p").unwrap();
        assert_eq!(paragraph.metrics.content_width, 200.0);
    }

    #[test]
    fn shorthand_edges_expand_correctly() {
        assert_eq!(
            Edges::from_shorthand("1px"),
            Edges {
                top: 1.0,
                right: 1.0,
                bottom: 1.0,
                left: 1.0
            }
        );
        assert_eq!(
            Edges::from_shorthand("1px 2px"),
            Edges {
                top: 1.0,
                right: 2.0,
                bottom: 1.0,
                left: 2.0
            }
        );
        assert_eq!(
            Edges::from_shorthand("1px 2px 3px 4px"),
            Edges {
                top: 1.0,
                right: 2.0,
                bottom: 3.0,
                left: 4.0
            }
        );
    }
}
