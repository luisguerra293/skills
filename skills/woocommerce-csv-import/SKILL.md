---
name: woocommerce-csv-import
description: Explains how to import, update, and troubleshoot product CSV files in WooCommerce using the built-in Product CSV Importer. Use when the user asks how to import products from a .csv into WooCommerce, how to format or fix a product CSV, how to bulk-update products, how to import variable products and variations, or why an import failed or skipped rows.
---

# Importing a CSV into WooCommerce

This skill covers the **built-in WooCommerce Product CSV Importer** (core plugin, free). It does not cover the premium Product CSV Import Suite or third-party importers; if the user uses one of those, say so and point them to that plugin's own docs.

Primary sources (check these if the user's WooCommerce version is newer than the docs below):
- https://woocommerce.com/document/product-csv-importer-exporter/
- https://github.com/woocommerce/woocommerce/wiki/Product-CSV-Import-Schema

Version notes used throughout: WooCommerce 11.1 added creating variations during an update import and single-import simple-to-variable conversion; 11.2 added matching by Global Unique ID (GTIN/UPC/EAN/ISBN). Ask the user their version if it matters (WooCommerce > Status, or Plugins list).

## Workflow overview

1. Back up the store (and test on staging for anything large or risky).
2. Build or obtain a valid UTF-8 CSV that follows the schema.
3. Run the importer: Products > All Products > Import.
4. Map columns, run, wait, review the report.
5. Spot-check products on the front end and in the admin.

## Step 1: Create the CSV

Three ways to start:
- **Export** a few products from an existing store (Products > All Products > Export). An exported file already follows the schema, so it is the safest template.
- Download the **sample product CSV** from the WooCommerce GitHub repo (`plugins/woocommerce/sample-data`) and replace the example values, keeping the column names.
- Build your own using the schema table below.

Editors the docs recommend: Google Sheets, Apache OpenOffice Calc, LibreOffice Calc, Numbers for macOS. Whatever you use, save/export as **UTF-8 CSV** and re-open the saved file to check that the spreadsheet did not alter formatting or encoding (Excel is the usual culprit; use "CSV UTF-8 (Comma delimited)").

### General formatting rules

- UTF-8 encoding.
- Dates use the store's local timezone.
- Booleans: `1` = true, `0` = false.
- Multiple values in one field are separated by commas. Wrap a value in double quotes if it contains a comma.
- To keep a comma inside a single value (e.g. one category called `Places, People, Cities`), escape each comma with a backslash: `Places\, People\, Cities`.
- Reference an existing product by ID with the `id:` prefix (`id:100`). Reference by SKU with no prefix (`SKU101`).
- Taxonomy hierarchy uses `>`; separate terms with commas (`Electronics, Home goods > Audio`).
- `Published` controls status: `1` published, `0` private, `-1` draft, `2` pending review (`true`/`false` also work for published/draft).
- You cannot assign a specific post ID to a new product. WooCommerce uses the next available ID regardless of the CSV.
- Custom meta must be plain text (no JSON or serialized data).

### Images

- Images must already be in the Media Library or reachable online. External URLs are downloaded into the Media Library.
- The first image in the `Images` column is the featured image; the rest form the gallery.
- If the filename already exists in the Media Library you can reference it by name.
- Some hosts block the request, require authorization, or return an HTML page instead of an image. If an image fails, upload it to the Media Library or get a direct image URL.
- The core importer cannot add or update image alt text.

### Column schema (core importer)

| Column | Example | Notes |
|---|---|---|
| `ID` | `100` | Identifies an existing product to update. Unmatched ID = row skipped (no fallback). Cannot set IDs for new products. |
| `Type` | `simple` | `simple`, `variable`, `grouped`, `external`, `variation`, `virtual`, `downloadable`. Multiple types comma-separated (e.g. `simple, virtual`). |
| `SKU` | `woo-headphones` | Used for matching and repeat imports. Not auto-generated for blank values per the current docs (an older wiki page says it is; trust the main docs and always supply SKUs). |
| `GTIN, UPC, EAN, or ISBN` | `0123456789012` | Maps to Global Unique ID (WooCommerce 11.2+). Defaults to "Do not import" in mapping; select it manually. |
| `Name` | `Headphones` | Required. |
| `Published` | `1` | See status values above. |
| `Is featured?` | `1` | 1/0. |
| `Visibility in catalog` | `visible` | `visible`, `catalog`, `search`, `hidden`. |
| `Short description` / `Description` | text | |
| `Date sale price starts` / `ends` | `2026-06-07` | Start-of-day / end-of-day. Blank = no date. |
| `Tax status` | `taxable` | `taxable`, `shipping`, `none`. |
| `Tax class` | `standard` | Slug of an existing tax class. |
| `In stock?` | `1` | 1/0. |
| `Stock` | `20` | A number turns on stock management. Blank = stock management off. `parent` on a variation inherits. |
| `Low stock amount` | `3` | Blank or number. |
| `Backorders allowed?` | `1` | `1`, `0`, or `notify`. |
| `Sold individually?` | `1` | 1/0. |
| `Weight (unit)`, `Length (unit)`, `Width (unit)`, `Height (unit)` | `100` | Numbers only. |
| `Allow customer reviews?` | `1` | 1/0. |
| `Purchase note` | text | |
| `Regular price` / `Sale price` | `24.99` / `20.99` | Plain numbers, no currency symbols. |
| `Categories` | `Electronics, Home goods > Audio` | `>` for hierarchy. |
| `Tags` | `Wireless, Audio` | |
| `Shipping class` | `Standard` | Name of the shipping class. |
| `Images` | `https://example.com/a.jpg, https://example.com/b.jpg` | First = featured. |
| `Download limit` / `Download expiry days` | `1` | `n/a` or a number. |
| `Parent` | `id:100` or `woo-headphones` | Parent of a variation. |
| `Grouped products`, `Upsells`, `Cross-sells` | `id:100, id:101` or `sku-1, sku-2` | IDs prefixed with `id:`. |
| `External URL`, `Button text` | URL / text | For external products. |
| `Position` | `1` | Menu order. |
| `Attribute 1 name` | `Color` | Matches a global attribute if one exists, else creates a product-level attribute. Add `Attribute 2 ...` etc. "Used for variations" is set automatically. |
| `Attribute 1 value(s)` | `Blue, Red, Green` | Parent lists all values; a variation row gives one (first is used if several). Empty on a variation = "any". |
| `Attribute 1 default` | `Blue` | Default for variable products. |
| `Attribute 1 visible` | `1` | Mapping screen label: "Attribute visibility". |
| `Attribute 1 global` | `1` | Mapping screen label: "Is a global attribute?". |
| `Download 1 name`, `Download 1 URL` | `Download 1`, `url.zip` | Repeat with 2, 3... |
| `meta:your_key` | `meta:product_depth` | Custom meta. If not auto-mapped, choose **Import as meta**. |

Unrecognized columns are not imported by default.

## Step 2: Import new products

1. Go to **Products > All Products**.
2. Click **Import** (next to Add new product) to open the **Upload CSV file** screen.
3. Click **Choose File** and select your CSV (or TXT). Alternative: open **Show advanced options** and enter the path of a CSV already on the server. **Continue** stays disabled until a file or path is provided.
4. Leave **Update existing products** unchecked (when checked, matching rows are updated instead; see below).
5. Click **Continue** to reach **Column mapping**. Recognized columns are mapped automatically. Fix any wrong mapping with the dropdowns, and set columns to ignore to **Do not import**.
6. Click **Run the importer**.
7. Do **not** refresh or leave the page while it runs.
8. Review the completion report for failed or skipped rows.

Note: with **Update existing products** unchecked, rows whose ID or SKU already exist are skipped.

## Step 3: Update existing products in bulk

Use for price changes, sale scheduling, adding a brand, changing tax class, or syncing between stores.

1. Prepare a CSV with an `ID` or `SKU` for each product (or, on WooCommerce 11.2+, a mapped Global Unique ID when both ID and SKU are blank).
2. Products > All Products > Import > choose file.
3. Check **Update existing products**.
4. Continue to column mapping. For Global Unique ID matching, map your column to **GTIN, UPC, EAN, or ISBN**.
5. Run the importer and review the report.

Matching rules:
- Rows match by `ID` or `SKU`.
- A supplied ID or SKU takes precedence even if unmatched; WooCommerce then does **not** fall back to Global Unique ID.
- Unmatched ID: row skipped. Unmatched SKU: skipped unless it qualifies as a new variation.
- With Global Unique ID matching, if the row's `Type` differs from the matched product's type, the row fails (blank `Type` avoids the check). Use ID or SKU for simple-to-variable conversion.
- Tip: export the products first, edit the export, and re-import it. This keeps column names and identifiers correct.

## Step 4: Variable products and variations

Structure: one parent row (`Type` = `variable`) listing all attribute values, then one row per variation (`Type` = `variation`) with one value each.

| Row | Type | SKU | Parent | Attribute 1 name | Attribute 1 value(s) | Attribute 1 visible | Attribute 1 global |
|---|---|---|---|---|---|---|---|
| Parent | `variable` | `tshirt` | | `Size` | `S, M` | `1` | `0` |
| Variation | `variation` | `tshirt-s` | `tshirt` | `Size` | `S` | `1` | `0` |
| Variation | `variation` | `tshirt-m` | `tshirt` | `Size` | `M` | `1` | `0` |

Rules:
- Each variation needs a **unique SKU** (or, on 11.2+, a usable Global Unique ID with blank SKU), an empty `ID`, and `Parent` set to the parent SKU or `id:123`.
- Attribute names and values must be spelled identically in parent and variation rows. Normalize case and whitespace (`L`, `l`, `Large` -> one value).
- `Attribute 1 global` = `0` for a product-level attribute, `1` for an existing global attribute.
- Put the parent row **before** its variation rows.
- Adding new variations to an existing variable product via an update import (11.1+): leave `ID` empty, `Type` = `variation`, `Parent` = parent SKU or `id:123`, attributes must match the parent's.

### Converting an existing simple product to variable

1. Back up or use staging. Export the simple product (it needs a SKU and price).
2. In the CSV keep the product row, change its `Type` from `simple` to `variable`, add attribute columns with all values, then add one row per variation.
3. **WooCommerce 11.1+ with parent row first:** check **Update existing products** and import once. Map `SKU`.
4. **Older versions, or row order not guaranteed:** do two imports.
   - Import 1: only the parent row, **Update existing products** checked.
   - Import 2: only the variation rows, **Update existing products** unchecked.
5. Open the product > **Variations** tab and confirm variations, prices, and stock. A published product needs enabled, priced variations to be purchasable.

### Supplier CSVs

Supplier files rarely match the schema. Before importing: pick a stable parent identifier, give each variation a unique SKU, normalize headers and attribute values, remove supplier-only columns, formulas, and currency symbols, save as UTF-8 CSV, then test one parent with a few variations on staging before the full file. Do not repeatedly import the full file until the small test works.

## Step 5: Verify

- Read the importer's report for skipped/failed rows and reasons.
- Open a sample of products: price, stock, categories, images, attributes, variations.
- Check the product on the storefront.

## Troubleshooting

**Rows skipped or products missing**
- A product with that SKU/ID exists and **Update existing products** was off.
- Columns or values do not match the schema.
- `Published` value gave an unexpected status (`1`, `0`, `-1`, `2`).
- Plugin or theme conflict interrupting the import (test with plugins deactivated).
- File too big for one request: split into smaller batches.

**"Sorry, this file type is not permitted for security reasons."**
WordPress can misidentify a CSV (e.g. when it contains HTML). Confirm the file is a real CSV, then upload it by SFTP/file manager to the site's `uploads` folder and enter that server path under **Show advanced options**. If that fails too, ask the host to check allowed file types and upload configuration.

**Upload size limit ("Maximum size" on the upload screen)**
Set at the server level; only the host can raise it.

**Large catalogs: timeouts, memory errors, import stalls**
- Back up, test on staging, and split the CSV into batches (e.g. `products-1.csv`, `products-2.csv`) so failures are easy to locate.
- "Allowed memory size exhausted" or timeouts mean the server's PHP memory limit or execution time is too low; ask the host to raise them. A WordPress.org support reply suggested a PHP time limit of 1200 and memory limit of 512M as a starting point (community guidance, not an official requirement).
- Third-party sources report problems appearing at a few hundred to a couple of thousand rows on shared hosting; treat that as anecdotal.
- For very large or custom-field-heavy imports the docs point to the premium Product CSV Import Suite.

**Garbled characters**
Re-save as UTF-8. Excel is the most common source of bad encoding.

**Attributes not linking to variations**
Check name/value spelling matches between parent and variation rows, and that the parent lists every value.

**Variations not created**
Unique SKU per variation, correct `Parent`, matching attributes, and (single-import method) parent row before variation rows.

## Related: export

Products > All Products > **Export**: choose columns, product types, categories, optionally **Yes, export all custom meta** (columns prefixed `meta:`), then **Generate CSV**. To export a subset, select products in the list and click **Export X selected**. Exported variation names may omit attribute values when a product has 3+ attributes, or 2+ attributes with a multi-word attribute name; that is expected.

## How to answer the user

- Ask (only if it changes the answer): new products or updates? simple or variable? WooCommerce version? large file?
- Give the exact menu path and button labels above.
- Offer to build or sanity-check their CSV against the schema if they paste or attach one.
- Remind them to back up first.
