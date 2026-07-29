from django.core.management import BaseCommand

import exercises
from exercises.models import Exercise

EXERCISES = [
    {
        "name": "Barbell Bench Press",
        "description": "Horizontal barbell press performed on a flat bench.",
        "muscle_groups": ["chest", "triceps", "shoulders"],
        "equipment": ["barbell", "bench", "squat_rack"],
    },
    {
        "name": "Incline Barbell Bench Press",
        "description": "Incline press emphasizing the upper chest and front shoulders.",
        "muscle_groups": ["chest", "shoulders", "triceps"],
        "equipment": ["barbell", "bench", "squat_rack"],
    },
    {
        "name": "Dumbbell Bench Press",
        "description": "Flat bench press performed with a dumbbell in each hand.",
        "muscle_groups": ["chest", "triceps", "shoulders"],
        "equipment": ["dumbbell", "bench"],
    },
    {
        "name": "Incline Dumbbell Press",
        "description": "Incline dumbbell press emphasizing the upper chest.",
        "muscle_groups": ["chest", "shoulders", "triceps"],
        "equipment": ["dumbbell", "bench"],
    },
    {
        "name": "Dumbbell Chest Fly",
        "description": "Chest isolation movement performed by opening and closing the arms.",
        "muscle_groups": ["chest", "shoulders"],
        "equipment": ["dumbbell", "bench"],
    },
    {
        "name": "Cable Crossover",
        "description": "Cable chest isolation exercise performed by bringing the arms together.",
        "muscle_groups": ["chest", "shoulders"],
        "equipment": ["cable"],
    },
    {
        "name": "Chest Press Machine",
        "description": "Machine-based horizontal pressing exercise.",
        "muscle_groups": ["chest", "triceps", "shoulders"],
        "equipment": ["machine"],
    },
    {
        "name": "Push-Up",
        "description": "Bodyweight horizontal pressing exercise.",
        "muscle_groups": ["chest", "triceps", "shoulders", "core"],
        "equipment": ["none"],
    },
    {
        "name": "Pull-Up",
        "description": "Vertical bodyweight pulling exercise using an overhand grip.",
        "muscle_groups": ["back", "biceps", "forearms"],
        "equipment": ["pull_up_bar"],
    },
    {
        "name": "Chin-Up",
        "description": "Vertical bodyweight pulling exercise using an underhand grip.",
        "muscle_groups": ["back", "biceps", "forearms"],
        "equipment": ["pull_up_bar"],
    },
    {
        "name": "Lat Pulldown",
        "description": "Vertical cable pull targeting the back.",
        "muscle_groups": ["back", "biceps", "forearms"],
        "equipment": ["cable"],
    },
    {
        "name": "Barbell Bent-Over Row",
        "description": "Horizontal barbell pull performed from a hinged position.",
        "muscle_groups": ["back", "biceps", "forearms", "core"],
        "equipment": ["barbell"],
    },
    {
        "name": "One-Arm Dumbbell Row",
        "description": "Single-arm horizontal rowing movement.",
        "muscle_groups": ["back", "biceps", "forearms"],
        "equipment": ["dumbbell", "bench"],
    },
    {
        "name": "Seated Cable Row",
        "description": "Horizontal cable row performed from a seated position.",
        "muscle_groups": ["back", "biceps", "forearms"],
        "equipment": ["cable"],
    },
    {
        "name": "Chest-Supported Dumbbell Row",
        "description": "Dumbbell row performed with the torso supported on an incline bench.",
        "muscle_groups": ["back", "biceps", "forearms"],
        "equipment": ["dumbbell", "bench"],
    },
    {
        "name": "Straight-Arm Pulldown",
        "description": "Cable isolation movement emphasizing shoulder extension and the back.",
        "muscle_groups": ["back", "triceps"],
        "equipment": ["cable"],
    },
    {
        "name": "Barbell Overhead Press",
        "description": "Standing vertical press performed with a barbell.",
        "muscle_groups": ["shoulders", "triceps", "core"],
        "equipment": ["barbell", "squat_rack"],
    },
    {
        "name": "Dumbbell Shoulder Press",
        "description": "Vertical press performed with dumbbells.",
        "muscle_groups": ["shoulders", "triceps"],
        "equipment": ["dumbbell", "bench"],
    },
    {
        "name": "Smith Machine Shoulder Press",
        "description": "Vertical shoulder press using a fixed bar path.",
        "muscle_groups": ["shoulders", "triceps"],
        "equipment": ["smith_machine", "bench"],
    },
    {
        "name": "Dumbbell Lateral Raise",
        "description": "Shoulder isolation exercise raising the arms out to the sides.",
        "muscle_groups": ["shoulders"],
        "equipment": ["dumbbell"],
    },
    {
        "name": "Cable Lateral Raise",
        "description": "Lateral shoulder raise performed against cable resistance.",
        "muscle_groups": ["shoulders"],
        "equipment": ["cable"],
    },
    {
        "name": "Dumbbell Front Raise",
        "description": "Shoulder isolation exercise raising the arms forward.",
        "muscle_groups": ["shoulders"],
        "equipment": ["dumbbell"],
    },
    {
        "name": "Reverse Dumbbell Fly",
        "description": "Rear shoulder and upper-back isolation movement.",
        "muscle_groups": ["shoulders", "back"],
        "equipment": ["dumbbell", "bench"],
    },
    {
        "name": "Face Pull",
        "description": "Cable pull toward the face targeting the rear shoulders and upper back.",
        "muscle_groups": ["shoulders", "back"],
        "equipment": ["cable"],
    },
    {
        "name": "Barbell Curl",
        "description": "Standing elbow-flexion exercise performed with a straight barbell.",
        "muscle_groups": ["biceps", "forearms"],
        "equipment": ["barbell"],
    },
    {
        "name": "EZ-Bar Curl",
        "description": "Standing curl performed with an angled EZ bar.",
        "muscle_groups": ["biceps", "forearms"],
        "equipment": ["ez_bar"],
    },
    {
        "name": "Dumbbell Curl",
        "description": "Elbow-flexion exercise performed with dumbbells.",
        "muscle_groups": ["biceps", "forearms"],
        "equipment": ["dumbbell"],
    },
    {
        "name": "Hammer Curl",
        "description": "Dumbbell curl performed with a neutral grip.",
        "muscle_groups": ["biceps", "forearms"],
        "equipment": ["dumbbell"],
    },
    {
        "name": "Incline Dumbbell Curl",
        "description": "Dumbbell curl performed while lying against an incline bench.",
        "muscle_groups": ["biceps", "forearms"],
        "equipment": ["dumbbell", "bench"],
    },
    {
        "name": "Cable Curl",
        "description": "Elbow-flexion exercise performed against cable resistance.",
        "muscle_groups": ["biceps", "forearms"],
        "equipment": ["cable"],
    },
    {
        "name": "Close-Grip Bench Press",
        "description": "Narrow-grip bench press emphasizing the triceps.",
        "muscle_groups": ["triceps", "chest", "shoulders"],
        "equipment": ["barbell", "bench", "squat_rack"],
    },
    {
        "name": "Cable Triceps Pushdown",
        "description": "Cable elbow-extension exercise performed from a standing position.",
        "muscle_groups": ["triceps"],
        "equipment": ["cable"],
    },
    {
        "name": "Overhead Cable Triceps Extension",
        "description": "Overhead elbow-extension exercise using cable resistance.",
        "muscle_groups": ["triceps"],
        "equipment": ["cable"],
    },
    {
        "name": "EZ-Bar Skull Crusher",
        "description": "Lying elbow-extension exercise performed with an EZ bar.",
        "muscle_groups": ["triceps"],
        "equipment": ["ez_bar", "bench"],
    },
    {
        "name": "Dumbbell Overhead Triceps Extension",
        "description": "Overhead elbow-extension exercise performed with a dumbbell.",
        "muscle_groups": ["triceps"],
        "equipment": ["dumbbell"],
    },
    {
        "name": "Parallel Bar Dip",
        "description": "Bodyweight pressing exercise performed on parallel bars.",
        "muscle_groups": ["triceps", "chest", "shoulders"],
        "equipment": ["dip_bars"],
    },
    {
        "name": "Barbell Back Squat",
        "description": "Barbell squat performed with the bar positioned across the upper back.",
        "muscle_groups": ["quadriceps", "glutes", "hamstrings", "core"],
        "equipment": ["barbell", "squat_rack"],
    },
    {
        "name": "Barbell Front Squat",
        "description": "Barbell squat performed with the bar supported across the front shoulders.",
        "muscle_groups": ["quadriceps", "glutes", "core"],
        "equipment": ["barbell", "squat_rack"],
    },
    {
        "name": "Goblet Squat",
        "description": "Squat performed while holding a weight in front of the torso.",
        "muscle_groups": ["quadriceps", "glutes", "core"],
        "equipment": ["dumbbell"],
    },
    {
        "name": "Leg Press",
        "description": "Machine-based compound leg pressing exercise.",
        "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
        "equipment": ["machine"],
    },
    {
        "name": "Leg Extension",
        "description": "Machine-based knee-extension isolation exercise.",
        "muscle_groups": ["quadriceps"],
        "equipment": ["machine"],
    },
    {
        "name": "Bulgarian Split Squat",
        "description": "Single-leg squat performed with the rear foot elevated.",
        "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
        "equipment": ["dumbbell", "bench"],
    },
    {
        "name": "Walking Lunge",
        "description": "Alternating forward lunges performed while moving across the floor.",
        "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
        "equipment": ["dumbbell"],
    },
    {
        "name": "Romanian Deadlift",
        "description": "Hip-hinge exercise emphasizing the hamstrings and glutes.",
        "muscle_groups": ["hamstrings", "glutes", "back", "forearms"],
        "equipment": ["barbell"],
    },
    {
        "name": "Conventional Deadlift",
        "description": "Barbell pull from the floor using a conventional stance.",
        "muscle_groups": ["back", "glutes", "hamstrings", "quadriceps", "forearms"],
        "equipment": ["barbell"],
    },
    {
        "name": "Sumo Deadlift",
        "description": "Barbell deadlift performed with a wide stance.",
        "muscle_groups": ["glutes", "quadriceps", "hamstrings", "back", "forearms"],
        "equipment": ["barbell"],
    },
    {
        "name": "Trap-Bar Deadlift",
        "description": "Deadlift performed from inside a hexagonal trap bar.",
        "muscle_groups": ["quadriceps", "glutes", "hamstrings", "back", "forearms"],
        "equipment": ["trap_bar"],
    },
    {
        "name": "Seated Leg Curl",
        "description": "Machine-based knee-flexion exercise targeting the hamstrings.",
        "muscle_groups": ["hamstrings"],
        "equipment": ["machine"],
    },
    {
        "name": "Lying Leg Curl",
        "description": "Hamstring curl performed lying face down on a machine.",
        "muscle_groups": ["hamstrings"],
        "equipment": ["machine"],
    },
    {
        "name": "Barbell Hip Thrust",
        "description": "Hip-extension exercise performed with the upper back supported.",
        "muscle_groups": ["glutes", "hamstrings"],
        "equipment": ["barbell", "bench"],
    },
    {
        "name": "Glute Bridge",
        "description": "Bodyweight hip-extension exercise performed from the floor.",
        "muscle_groups": ["glutes", "hamstrings", "core"],
        "equipment": ["none"],
    },
    {
        "name": "Barbell Good Morning",
        "description": "Barbell hip-hinge exercise performed with the bar across the upper back.",
        "muscle_groups": ["hamstrings", "glutes", "back", "core"],
        "equipment": ["barbell", "squat_rack"],
    },
    {
        "name": "Standing Calf Raise",
        "description": "Plantar-flexion exercise performed from a standing position.",
        "muscle_groups": ["calves"],
        "equipment": ["machine"],
    },
    {
        "name": "Seated Calf Raise",
        "description": "Calf exercise performed from a seated position.",
        "muscle_groups": ["calves"],
        "equipment": ["machine"],
    },
    {
        "name": "Dumbbell Wrist Curl",
        "description": "Forearm flexion exercise performed with dumbbells.",
        "muscle_groups": ["forearms"],
        "equipment": ["dumbbell", "bench"],
    },
    {
        "name": "Reverse Barbell Curl",
        "description": "Curl performed with an overhand grip to emphasize the forearms.",
        "muscle_groups": ["forearms", "biceps"],
        "equipment": ["barbell"],
    },
    {
        "name": "Farmer's Carry",
        "description": "Loaded carry performed while walking with weights at the sides.",
        "muscle_groups": ["forearms", "core", "shoulders", "back"],
        "equipment": ["dumbbell"],
    },
    {
        "name": "Plank",
        "description": "Static bodyweight exercise maintaining a rigid torso position.",
        "muscle_groups": ["core", "shoulders"],
        "equipment": ["none"],
    },
    {
        "name": "Side Plank",
        "description": "Static lateral core exercise supported on one arm.",
        "muscle_groups": ["core", "shoulders"],
        "equipment": ["none"],
    },
    {
        "name": "Cable Crunch",
        "description": "Weighted spinal-flexion exercise using cable resistance.",
        "muscle_groups": ["core"],
        "equipment": ["cable"],
    },
    {
        "name": "Hanging Leg Raise",
        "description": "Core exercise performed while hanging from a pull-up bar.",
        "muscle_groups": ["core", "forearms"],
        "equipment": ["pull_up_bar"],
    },
    {
        "name": "Russian Twist",
        "description": "Rotational core exercise performed from a seated position.",
        "muscle_groups": ["core"],
        "equipment": ["medicine_ball"],
    },
    {
        "name": "Pallof Press",
        "description": "Anti-rotation core exercise performed against cable resistance.",
        "muscle_groups": ["core"],
        "equipment": ["cable"],
    },
    {
        "name": "Kettlebell Swing",
        "description": "Explosive hip-hinge movement performed with a kettlebell.",
        "muscle_groups": ["glutes", "hamstrings", "back", "core", "shoulders"],
        "equipment": ["kettlebell"],
    },
    {
        "name": "Burpee",
        "description": "Full-body conditioning exercise combining a squat, plank and jump.",
        "muscle_groups": ["full_body", "quadriceps", "chest", "shoulders", "core"],
        "equipment": ["none"],
    },
    {
        "name": "Rowing Machine",
        "description": "Cardiovascular rowing exercise performed on an ergometer.",
        "muscle_groups": ["full_body", "back", "quadriceps", "core"],
        "equipment": ["cardio_machine"],
    },
    {
        "name": "Treadmill Running",
        "description": "Running or jogging performed on a treadmill.",
        "muscle_groups": ["full_body", "quadriceps", "hamstrings", "calves"],
        "equipment": ["cardio_machine"],
    },
    {
        "name": "Stationary Cycling",
        "description": "Cardiovascular cycling performed on a stationary bike.",
        "muscle_groups": ["quadriceps", "hamstrings", "glutes", "calves"],
        "equipment": ["cardio_machine"],
    },
]

class Command(BaseCommand):
    help = 'Fill exercises table'

    def handle(self, *args, **options):
        for_bulk_create = []
        for exercise in EXERCISES:
            for_bulk_create.append(
                Exercise(
                    name=exercise["name"],
                    description=exercise["description"],
                    muscle_groups=exercise["muscle_groups"],
                    equipment=exercise["equipment"],
                )
            )
        Exercise.objects.bulk_create(for_bulk_create)
        created = len(for_bulk_create)
        self.stdout.write(f'"{help}" Command executed successfully. {created} exercises created.')