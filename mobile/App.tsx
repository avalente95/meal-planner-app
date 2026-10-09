import { useEffect, useState } from "react";
import { StatusBar } from "expo-status-bar";
import { StyleSheet, Text, View } from "react-native";
import { config } from "./src/config";

export default function App() {
  const [result, setResult] = useState("loading...");

  useEffect(() => {
    async function check() {
      try {
        const health = await fetch(`${config.apiUrl}/health`);
        const recipes = await fetch(`${config.apiUrl}/api/v1/recipes`, {
          headers: { "X-API-Key": config.apiKey },
        });
        const ingredients = await fetch(`${config.apiUrl}/api/v1/ingredients`, {
          headers: { "X-API-Key": config.apiKey },
        });
        setResult(`health: ${health.status}, recipes: ${ingredients.status}`);
      } catch {
        setResult("network error");
      }
    }
    check();
  }, []);

  return (
    <View style={styles.container}>
      <Text>{result}</Text>
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center" },
});