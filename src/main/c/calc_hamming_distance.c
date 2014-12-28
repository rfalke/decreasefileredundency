#include <stdio.h>
#include <assert.h>
#include <stdlib.h>
#include <stdint.h>
#include <ctype.h>
#include <string.h>
#include <sys/time.h>

#define PRINT_DEBUG_DATA 0

typedef unsigned char counter_t;
struct pair {
	int index;
	int score;
};

static uint64_t *data;
static char *available;
static int num_data;
static int max_dist;
static int num_to_output;
static int score_factors[16];
static counter_t *counters;
static struct pair *pairs;
static char *to_output;
static int technical;
static int quiet;

static int min(int x, int y)
{
	if (x < y)
		return x;
	return y;
}

static int max(int x, int y)
{
	if (x > y)
		return x;
	return y;
}

static void usage(const char *msg)
{
	fprintf(stderr,
		"Usage: calc_hamming_distance [-t] [-q] <input-file> <output-file>\n");
	fprintf(stderr, "Problem: %s\n", msg);
	exit(1);
}

static inline uint64_t simple_strtoul(const char *cp)
{
	const unsigned int base = 16;
	uint64_t result = 0;
	int i = 0;

	for (i = 0; i < 16; i++) {
		uint64_t value;

		assert(isxdigit(*cp));
		value = isdigit(*cp) ? *cp - '0' : toupper(*cp) - 'A' + 10;
		assert(value < base);
		result = result * base + value;
		cp++;
	}
	return result;
}

static void read_data(FILE * data_input)
{
	char line_buffer[4096], *tmp;
	int line;

	tmp = fgets(line_buffer, 4096, data_input);
	assert(tmp == line_buffer);

	if (sscanf
	    (line_buffer,
	     "%d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d %d",
	     &num_data, &max_dist, &num_to_output, score_factors,
	     score_factors + 1, score_factors + 2, score_factors + 3,
	     score_factors + 4, score_factors + 5, score_factors + 6,
	     score_factors + 7, score_factors + 8, score_factors + 9,
	     score_factors + 10, score_factors + 11, score_factors + 12,
	     score_factors + 13, score_factors + 14,
	     score_factors + 15) != 3 + 16) {
		usage("wrong number of parameters in first line");
	}
	data = malloc(sizeof(uint64_t) * num_data);
	available = malloc(sizeof(char) * num_data);
	to_output = malloc(sizeof(char) * num_data);
	memset(to_output, 0, sizeof(char) * num_data);
	counters = malloc(sizeof(counter_t) * num_data * 16);
	memset(counters, 0, sizeof(counter_t) * num_data * 16);
	assert(max_dist >= 0);
	assert(max_dist <= 15);
	assert(num_to_output <= num_data);
	for (int i = 0; i < 16; i++) {
		assert(score_factors[i] > 0);
	}

	for (line = 0; line < num_data; line++) {
		tmp = fgets(line_buffer, 4096, data_input);
		assert(tmp == line_buffer);
		if (strncmp(line_buffer, "na", 2) == 0) {
			available[line] = 0;
			data[line] = line * 13;
		} else {
			available[line] = 1;
			assert(strlen(line_buffer) == 17);
			line_buffer[16] = '\0';
			uint64_t val = simple_strtoul(line_buffer);
			data[line] = val;
		}
//      printf("line=%d = '%s' = %lx avail=%d\n", line, line_buffer, (*data)[line], (*available)[line]);
	}
}

#define ADD(D, INDEX)           {counter_t old = counters[16*INDEX+D]; if(old!=255) counters[16*INDEX+D]++;}
#define INNER(X,Y) 				{int sx=X; int sy=Y; uint64_t distance = __builtin_popcountll(to_compare ^ (data[sy])); \
                   				if (distance <= max_dist && available[sy]) { \
                   				    ADD(distance, sx); \
                                    ADD(distance, sy); \
                                }}

static void compare_pairs_inner()
{
	struct timeval start_time, last_update;
	gettimeofday(&start_time, NULL);
	gettimeofday(&last_update, NULL);

	float counter = 0;
	float total = ((float)num_data * num_data) / 2;
	for (int x = 0; x < num_data; x++) {
		uint64_t to_compare = data[x];
		if (available[x]) {
			int start = x + 1;
			int next_4 = min(((start - 1) / 4 + 1) * 4, num_data);
			int last_4 = max(num_data & (~3), start);
			if (0)
				printf
				    ("for %d begin=[%d-%d) end=[%d-%d) fast=[%d-%d)\n",
				     x, start, next_4, last_4, num_data, next_4,
				     last_4);
			for (int y = start; y < next_4; y++) {
				INNER(x, y);
			}
			for (int y = last_4; y < num_data; y++) {
				INNER(x, y);
			}
			for (int y = next_4; y < last_4; y += 4) {
				INNER(x, y + 0);
				INNER(x, y + 1);
				INNER(x, y + 2);
				INNER(x, y + 3);
			}
		}

		if (!quiet) {
			counter += num_data - x;
			struct timeval tm2;
			gettimeofday(&tm2, NULL);

			unsigned long long time_since_last_update =
			    1000 * (tm2.tv_sec - last_update.tv_sec) +
			    (tm2.tv_usec - last_update.tv_usec) / 1000;

			if (time_since_last_update > 200) {
				last_update = tm2;
				unsigned long long time_so_far_in_ms =
				    1000 * (tm2.tv_sec - start_time.tv_sec) +
				    (tm2.tv_usec - start_time.tv_usec) / 1000;
				float percent_done = counter / total;
				float time_so_far_in_sec =
				    time_so_far_in_ms / 1000.0;
				float total_time =
				    time_so_far_in_sec / percent_done;
				float remaining_time =
				    total_time * (1.0 - percent_done);

				fprintf(stderr,
					"Calculating hamming distances: %.0f/%.0f = %.2f%% [%llu secs used] [%d secs remaining]\r",
					counter / 100000000.0,
					total / 100000000.0,
					100.0 * percent_done,
					time_so_far_in_ms / 1000,
					(int)remaining_time);
			}
		}
	}
	if (!quiet) {
		struct timeval tm2;
		gettimeofday(&tm2, NULL);

		unsigned long long time_so_far_in_ms =
		    1000 * (tm2.tv_sec - start_time.tv_sec) +
		    (tm2.tv_usec - start_time.tv_usec) / 1000;
		fprintf(stderr,
			"Finished calculating hamming distances in %llu secs                                     \n",
			time_so_far_in_ms / 1000);
	}

}

static void compare_pairs()
{
	struct timeval tm1, tm2;
	gettimeofday(&tm1, NULL);

	compare_pairs_inner();

	gettimeofday(&tm2, NULL);
	unsigned long long time_in_ms =
	    1000 * (tm2.tv_sec - tm1.tv_sec) + (tm2.tv_usec -
						tm1.tv_usec) / 1000;
	if (technical) {
		float size = ((float)num_data * num_data) / 2;
		printf
		    ("required %llu ms = %f mio ops/s\n",
		     time_in_ms, (size / 1000000.0) / (time_in_ms / 1000.0));
	}
}

static void recalc_relevant_for_output(FILE * output)
{
	for (int k = 0; k < num_data; k++) {
		int x = pairs[k].index;
		if (to_output[x]) {
			uint64_t to_compare = data[x];
			assert(available[x]);
			fprintf(output, "%d: %d", x, pairs[k].score);
			long long counters[16] =
			    { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 };
			long long all_hits = 0;
			for (int y = 0; y < num_data; y++) {
				if (x == y)
					continue;
				uint64_t distance =
				    __builtin_popcountll(to_compare ^
							 (data[y]));
				if (distance <= max_dist && available[y]) {
					counters[distance]++;
					all_hits++;
				}
			}
			fprintf(output, " %lld=", all_hits);
			for (int i = 0; i < 16; i++) {
				if (i != 0)
					fprintf(output, ",");
				if (counters[i]) {
					fprintf(output, "%lld", counters[i]);
				}
			}

			for (int y = 0; y < num_data; y++) {
				if (x == y)
					continue;
				uint64_t distance =
				    __builtin_popcountll(to_compare ^
							 (data[y]));
				if (distance <= max_dist && available[y]) {
					fprintf(output, " %d:%ld", y, distance);
				}
			}
			fprintf(output, "\n");
		}
	}
}

static void print_counters()
{
#if PRINT_DEBUG_DATA
	for (int x = 0; x < num_data; x++) {
		if (available[x]) {
			printf("%d: ", x);
			for (int i = 0; i <= max_dist; i++) {
				if (counters[x * 16 + i])
					printf(" dist[%d]=%d", i,
					       counters[x * 16 + i]);
			}
			printf("\n");
		}
	}
#endif
}

#define COMPARE(a, b) (((a) > (b)) - ((a) < (b)))

static int sort_by_score_desc(const void *v1, const void *v2)
{
	const struct pair *p1 = v1;
	const struct pair *p2 = v2;
	if (p2->score == p1->score) {
		return COMPARE(p1->index, p2->index);
	}
	return COMPARE(p2->score, p1->score);
}

static void init_scores_and_sort()
{
	pairs = malloc(sizeof(struct pair) * num_data);
	for (int x = 0; x < num_data; x++) {
		int score = 0;
		if (available[x]) {
			for (int i = 0; i <= max_dist; i++) {
				score +=
				    score_factors[i] * counters[x * 16 + i];
			}
		}
		pairs[x].index = x;
		pairs[x].score = score;
	}
	qsort(pairs, num_data, sizeof(struct pair), sort_by_score_desc);
}

static void print_pairs()
{
#if PRINT_DEBUG_DATA

	for (int x = 0; x < num_data; x++) {
		printf("at %d index=%d with a score of %d\n", x, pairs[x].index,
		       pairs[x].score);
	}
#endif
}

static void mark_for_output()
{
	for (int x = 0; x < num_to_output; x++) {
		if (pairs[x].score) {
			to_output[pairs[x].index] = 1;
		}
	}
}

int main(int argc, char *argv[])
{
	int i = 1, remaining = argc - 1;
	if (remaining > 0 && strcmp(argv[i], "-t") == 0) {
		technical = 1;
		remaining--;
		i++;
	}
	if (remaining > 0 && strcmp(argv[i], "-q") == 0) {
		quiet = 1;
		remaining--;
		i++;
	}
	if (remaining > 0 && strcmp(argv[i], "-t") == 0) {
		technical = 1;
		remaining--;
		i++;
	}

	if (remaining != 2) {
		usage("wrong number of arguments");
	} else {
		FILE *data_input = fopen(argv[i], "r");
		assert(data_input);
		FILE *output = fopen(argv[i + 1], "w");
		assert(output);

		read_data(data_input);
		compare_pairs();
		print_counters();
		init_scores_and_sort();
		print_pairs();
		mark_for_output();
		recalc_relevant_for_output(output);

		return 0;
	}
}
