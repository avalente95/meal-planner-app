import { StatusBar } from "expo-status-bar";
import IngredientListScreen from "./src/screens/IngredientListScreen";

export default function App() {
  return (
    <>
      <IngredientListScreen />
      <StatusBar style="auto" />
    </>
  );
}