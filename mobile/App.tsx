import { ActivityIndicator, Button, View } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { AuthProvider, useAuth } from './src/lib/authContext';
import LoginScreen from './src/screens/LoginScreen';
import IngredientListScreen from './src/screens/IngredientListScreen';

const Stack = createNativeStackNavigator();

function Root() {
  const { session, loading, signOut } = useAuth();

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center' }}>
        <ActivityIndicator />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator>
        {session ? (
          <Stack.Screen
            name="Ingredients"
            component={IngredientListScreen}
            options={{
              title: 'Ingredients',
              headerRight: () => <Button title="Exit" onPress={signOut} />,
            }}
          />
        ) : (
          <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Root />
    </AuthProvider>
  );
}