# Build your first widget

In this tutorial you will turn a small CSV file into a widget and view it in your browser. It takes about ten minutes and assumes you have never used Widgetry before.

## Before you start

You need Python 3.11 or later and Widgetry installed. To check, run `widgetry --version`; it should print a version number such as `2.4.0`.

## Steps

1. Create a file named `pets.csv` with this content:

   ```
   name,species
   Miso,cat
   Biscuit,dog
   ```

2. Build the widget:

   ```
   widgetry build pets.csv
   ```

   Widgetry prints `Built 1 widget: pets.widget`.

3. Open the widget:

   ```
   widgetry open pets.widget
   ```

   Your browser opens a page with a two-row table.

## What you built

You now have `pets.widget`, a file you can share or embed. Next, try the reference page to see every option `build` accepts.
